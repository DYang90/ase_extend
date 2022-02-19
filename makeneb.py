# coding='utf8'
# 程序：使用ase进行NEB路径初始猜测
# 作者：$开发$
# 日期：2022.2.18

# 读取数据
def parse_args():
    # 使用argparse获取参数
    import argparse
    p = argparse.ArgumentParser()
    # 用nargs来让-i参数获取1个或多个结构的文件名。
    p.add_argument('-i', '--images', nargs='+',
                   type=str, help='Images defining path from initial to final state.')
    # 默认为6，因为大多服务器核心数是4的倍数。
    p.add_argument('-n', '--nimage', type=int, default=6,
                   help='Number of images in a band. Default: 6')
    # 是否写入XDATCAR。
    p.add_argument('-o', '--output', action='store_true',
                   help='Whether or not write XDATCAR.')
    # 插点方法，可选线性插点或idpp，默认用线性。
    p.add_argument('--method', type=str, choices=['linear', 'idpp'], default='linear',
                   help='Interpolate method to initial guess. Default: linear')
    # idpp插点最大迭代步数，默认是100。
    p.add_argument('--nstep', type=int, default=100,
                   help='Max number of iteration steps. Default: 100')
    # 弹簧常数，默认按照ase.neb.NEB的0.1。
    p.add_argument('--spring', type=float, default=0.1,
                   help='Fraction of spring force. Default: 0.1')
    # idpp插点迭代的力收敛域值，默认按照ase.neb.NEB的0.1。
    p.add_argument('--fmax', type=float, default=0.1,
                   help='Maximum force of converge thershould. Default: 0.1')
    # idpp插点迭代所使用的优化算法，默认为ase.optimize.MDMin。
    p.add_argument('--optimizer', type=str, choices=['MDMin', 'BFGS', 'LBFGS', 'FIRE'],
                   default='MDMin', help='Optimizer using in IDPP iteration. Default: MDMin')
    return p

# 数据处理
def neb_interpolate(args):
    # 通过ase.io读取始末结构。
    from ase import io
    # 只有一个轨迹文件的情形。
    if len(args.images) == 1:
        images = io.iread(args.images[0])
        images = list(images)
        initial = images[0]
        final = images[-1]
    # 使用两个结构的情形。
    elif len(args.images) == 2:
        initial = io.read(args.images[0])
        final = io.read(args.images[-1])
    else:
        initial = None
        final = None
        exit('Number of images must be a trajactory or two structures.')
    # 初始化路径，共nimage个结构。
    images = [initial]+[initial.copy() for i in range(args.nimage-2)]+[final]
    # 将多帧images转换为NEB对象。
    from ase.neb import NEB
    neb = NEB(images, k=args.spring)
    # 可以按照https://wiki.fysik.dtu.dk/ase/ase/neb.html，最终NEB中的image将被更新。
    if args.method == 'linear':
        neb.interpolate(method='linear')
    elif args.method == 'idpp':
        neb.interpolate()
        # 可选优化算法。
        from ase.optimize import MDMin, BFGS, LBFGS, FIRE
        index = {'MDMin': MDMin, 'BFGS': BFGS, 'LBFGS': LBFGS, 'FIRE': FIRE}
        neb.idpp_interpolate(
            fmax=args.fmax, optimizer=index[args.optimizer], steps=args.nstep)
    return images

# 输出结果
def write_guess(args, images):
    # 按编号建立文件夹，没文件夹的建文件夹，有文件夹的跳过。
    import os
    [os.mkdir('%02d' % i)
     for i in range(len(images)) if not os.path.exists('%02d' % i)]
    # 到对应目录去写入POSCAR文件。
    from ase import io
    [io.write('%02d/POSCAR' % i, images[i]) for i in range(len(images))]
    # 如果需要写入XDATCAR。
    if args.output:
        io.write('XDATCAR', images)
    # 如果需要导入MS可以使用，可以手动运行ase convert XDATCAR name.xtd进行转换。
    # XDATCAR也可以通过ase gui XDATCAR来进行预览。
# 主程序
if __name__ == '__main__':
    # 串联全部函数使用。
    # 读取参数
    p = parse_args()
    args = p.parse_args()
    # 若处理失败则显示菜单
    try:
        # 数据处理
        images = neb_interpolate(args)
        # 输出结果
        write_guess(args, images)
    except:
        p.print_help()
