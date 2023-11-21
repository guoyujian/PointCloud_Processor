from loguru import logger
from argparse import ArgumentParser
import os
import os.path as osp
from glob import glob

from open3d.cpu.pybind.visualization import VisualizerWithEditing

from extract_bag import BagExtractor
from merge_pointcloud import SimpleMerge, SimpleMergeWithoutOdometer
import open3d as o3d

def generate_res_dir_from_bag_filepath(bag_filepath: str):
    '''
    根据bag_filepath生成结果文件目录，并返回
    :param bag_filepath:
    :return:
    '''
    if not osp.exists(bag_filepath):
        logger.error(f'{bag_filepath} 不存在')
        return

    dir_basename = osp.basename(bag_filepath).replace('.bag', '')
    res_dir = osp.join(osp.dirname(bag_filepath), dir_basename)
    if not osp.exists(res_dir):
        os.mkdir(res_dir)
    else:
        logger.info(f'{res_dir} 目录已存在')
    logger.info(f'{bag_filepath}结果目录目录：{res_dir}')
    return bag_filepath, res_dir


def extract_single_bag(bag_filepath_and_res_dir: tuple):
    '''
    处理单个bag包，并把结果放在bag_dir/tmp中
    :param bag_filepath:
    :param bag_dir:
    :return:
    '''
    bag_filepath = bag_filepath_and_res_dir[0]
    res_dir = bag_filepath_and_res_dir[1]
    bag2pcd_dir = osp.join(res_dir, 'tmp') # 解析bag出的txt+pcd放在bag2pcd_dir中
    if not osp.exists(bag2pcd_dir):
        os.mkdir(bag2pcd_dir)
    BagExtractor(bag_filepath, bag2pcd_dir).run()
    return bag2pcd_dir, res_dir


def process_bag_dir(bag2pcd_dir_and_res_dir_list: tuple):
    '''
    merge point cloud
    :param bag_dir:
    :return:
    '''
    bag2pcd_dir = bag2pcd_dir_and_res_dir_list[0]
    res_dir = bag2pcd_dir_and_res_dir_list[1] # 存放合并后的pcd的目录

    merged_pcd_filepath = osp.join(res_dir, 'merged.pcd')
    # 简单拼接
    # SimpleMerge(bag2pcd_dir, merged_pcd_filepath).merge()

    SimpleMerge(bag2pcd_dir, merged_pcd_filepath).merge()
    SimpleMergeWithoutOdometer(bag2pcd_dir, merged_pcd_filepath).merge()
    return merged_pcd_filepath
    pass

#
# def show_pcd_with_editing(merged_pcd_filepath: str):
#     logger.info('请操作点云，并选择需要计算距离的点')
#
#     pcd: o3d.geometry.PointCloud = o3d.io.read_point_cloud(merged_pcd_filepath)
#     vis: VisualizerWithEditing = o3d.visualization.VisualizerWithEditing()
#     vis.create_window()
#     vis.add_geometry(pcd)
#     vis.run()  # user edit and picks points
#     picked_points_index = vis.get_picked_points()
#     cropped_pcd: o3d.cpu.pybind.geometry.Geometry = vis.get_cropped_geometry()
#     return cropped_pcd.PointCloud, picked_points_index



def main():
    parser = ArgumentParser(description="""
        本脚本实现从bag包解析到距离计算并保存截图
        1. 读取bag_dir中的所有bag解析到同级的同名目录的/tmp_dir下，例如xxx/a.bag，将解析结果存放到xxx/a/tmp_dir/下
        2. 依次读取tmp_dir中的pcd和txt，解析txt的转换矩阵并将其作用到pcd点云中
        3. 拼接点云，形成一个整体的pcd，存放到xxx/a/a.pcd
        """)
    parser.add_argument('bag_dir',
                        default='C:\\Users\\Administrator\\Desktop\\bag_test',
                        help='存放bag文件的文件夹')
    args = parser.parse_args()
    # 获得bag_dir下的所有bag文件
    bag_filepath_list = glob(osp.join(args.bag_dir, '*.bag'))
    if len(bag_filepath_list) == 0:
        logger.error(f'{args.bag_dir}文件夹下没有bag文件')
        return
    bag_filepath_and_res_dir_list = list(map(generate_res_dir_from_bag_filepath, bag_filepath_list))
    bag2pcd_dir_and_res_dir_list = list(map(extract_single_bag, bag_filepath_and_res_dir_list))
    merged_pcd_filepath_list = list(map(process_bag_dir, bag2pcd_dir_and_res_dir_list))
    logger.info(f'生成的pcd文件列表：{merged_pcd_filepath_list}')
    logger.info('处理完成')


if __name__ == '__main__':
    main()