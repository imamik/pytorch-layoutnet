import torch.nn as nn


def group_weight(module):
    # Group module parameters into two group
    # One need weight_decay and the other doesn't
    # Copy from
    # https://github.com/CSAILVision/semantic-segmentation-pytorch/blob/master/train.py
    group_decay = []
    group_no_decay = []
    for m in module.modules():
        if isinstance(m, nn.Linear):
            group_decay.append(m.weight)
            if m.bias is not None:
                group_no_decay.append(m.bias)
        elif isinstance(m, nn.modules.conv._ConvNd):
            group_decay.append(m.weight)
            if m.bias is not None:
                group_no_decay.append(m.bias)
        elif isinstance(m, nn.modules.batchnorm._BatchNorm):
            if m.weight is not None:
                group_no_decay.append(m.weight)
            if m.bias is not None:
                group_no_decay.append(m.bias)

    assert len(list(module.parameters())) == len(group_decay) + len(group_no_decay)
    return [dict(params=group_decay), dict(params=group_no_decay, weight_decay=.0)]


def adjust_learning_rate(optimizer, args):
    if args.cur_iter < args.warmup_iters:
        frac = args.cur_iter / args.warmup_iters
        step = args.lr - args.warmup_lr
        args.running_lr = args.warmup_lr + step * frac
    else:
        frac = (float(args.cur_iter) - args.warmup_iters) / (args.max_iters - args.warmup_iters)
        scale_running_lr = max((1. - frac), 0.) ** args.lr_pow
        args.running_lr = args.lr * scale_running_lr

    for param_group in optimizer.param_groups:
        param_group['lr'] = args.running_lr


class Statistic():
    '''
    For training statistic
    set winsz > 0 for running statitic
    '''
    def __init__(self, winsz=0):
        self.winsz = winsz
        self.cnt = 0
        self.weight = 0  # work only if winsz==0
        self.total = 0

    def update(self, val, weight=1):
        self.cnt += 1
        if self.winsz <= 0:
            self.weight += weight
            self.total += val * weight
        elif self.cnt > self.winsz:
            self.total += (val - self.total) / self.winsz
        else:
            self.total += (val - self.total) / self.cnt

    def __str__(self):
        return '%.6f' % float(self)

    def __float__(self):
        if self.winsz <= 0:
            return float(self.total / self.weight)
        else:
            return float(self.total)
