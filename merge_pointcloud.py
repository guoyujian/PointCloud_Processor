from abc import ABCMeta, abstractmethod
from glob import glob
import os.path as osp
import yaml
import numpy as np
from scipy.spatial.transform import Rotation as R
import open3d as o3d
from loguru import logger
from conf.pc_conf import MAX_DISTANCE, MIN_DISTANCE, ROTATE_CENTER, VOXEL_SIZE, NB_NEIGHBORS, STD_RATIO
from utils.math_utils import get_translation_and_rotation_matrix_from

class IMerge(metaclass=ABCMeta):
    def __init__(self, pcd_dir: str, pcd_filepath: str):
        super(IMerge, self).__init__()

        # self.pcds = [
        #     (
        #         o3d.io.read_point_cloud(pcd_filepath),
        #         self.get_translation_and_rotation_matrix_from(pcd_filepath[:-4] + '.txt')
        #     )
        #     for pcd_filepath in pcd_files
        # ]

    @abstractmethod
    def merge(self):
        pass





class SimpleMerge(IMerge):
    def __init__(self, pcd_dir: str, pcd_filepath: str):
        super().__init__(pcd_dir, pcd_filepath)
        self.pcd_filepath = pcd_filepath
        pcd_files = glob(osp.join(pcd_dir, '*.pcd'))
        self.pcd_files = [pcd_file for pcd_file in pcd_files if osp.exists(pcd_file[:-4] + '.txt')]
        logger.info(f'待合并的文件数：{len(self.pcd_files)}')

    def merge(self):
        logger.info(f"降采样：{VOXEL_SIZE}")
        txt_files = [pcd_filepath[:-4] + '.txt' for pcd_filepath in self.pcd_files]

        # 创建目标点云
        target_point_cloud = o3d.geometry.PointCloud()

        for i, (pcd_filepath, txt_filepath) in enumerate(zip(self.pcd_files, txt_files)):
            pcd: o3d.geometry.PointCloud = o3d.io.read_point_cloud(pcd_filepath)
            # 过滤小于最小值大于最大值的点
            points = np.asarray(pcd.points)
            # 计算每个点到坐标原点的L2范数
            distances = np.linalg.norm(points, axis=1)
            # 根据索引保留点
            point_cloud = pcd.select_by_index(
                np.where((distances >= MIN_DISTANCE) & (distances <= MAX_DISTANCE))[0])

            pcd = pcd.voxel_down_sample(VOXEL_SIZE)

            pcd, _ = pcd.remove_statistical_outlier(nb_neighbors=NB_NEIGHBORS,
                                                    std_ratio=STD_RATIO)  # 统计滤波
            translation_vector, rotation_matrix = get_translation_and_rotation_matrix_from(txt_filepath)
            # logger.info(f'before transformation: {np.asarray(pcd.points[:3])}')
            pcd.rotate(rotation_matrix, center=ROTATE_CENTER)
            # logger.info(f'after rotate: {np.asarray(pcd.points[:3])}')
            pcd.translate(translation_vector)  # 平移
            # logger.info(f'after translate: {np.asarray(pcd.points[:3])}')
            target_point_cloud += pcd

            logger.info(f"文件总数：{len(self.pcd_files)}, 处理完第{i + 1}个文件")
            pass
        target_point_cloud = target_point_cloud.voxel_down_sample(VOXEL_SIZE)
        o3d.io.write_point_cloud(self.pcd_filepath, target_point_cloud)
        logger.info(f'点云合并完成：{self.pcd_filepath}')


class SimpleMergeWithoutOdometer(IMerge):
    def __init__(self, pcd_dir: str, pcd_filepath: str):
        super().__init__(pcd_dir, pcd_filepath)
        self.pcd_filepath = pcd_filepath
        self.pcd_files = glob(osp.join(pcd_dir, '*.pcd'))
        logger.info(f'待合并的文件数：{len(self.pcd_files)}')

    def merge(self):
        logger.info(f"降采样：{VOXEL_SIZE}")

        # 创建目标点云
        target_point_cloud = o3d.geometry.PointCloud()

        for i, pcd_filepath in enumerate(self.pcd_files):
            # logger.info(f'{pcd_filepath}')
            point_cloud: o3d.geometry.PointCloud = o3d.io.read_point_cloud(pcd_filepath)
            target_point_cloud += point_cloud
            logger.info(f"文件总数：{len(self.pcd_files)}, 处理完第{i + 1}个文件")
            pass
        # target_point_cloud = target_point_cloud.voxel_down_sample(VOXEL_SIZE)
        o3d.io.write_point_cloud(self.pcd_filepath, target_point_cloud)
        logger.info(f'点云合并完成：{self.pcd_filepath}')


def main():
    SimpleMerge(r"C:\work\point_cloud\bag-files\2023-9-5-18-35-13",
                r"C:\Users\Administrator\Desktop\test.pcd").merge()
    o3d.visualization.draw_geometries(
        [o3d.io.read_point_cloud(r"C:\Users\Administrator\Desktop\test.pcd")]
    )

    # pcd = o3d.io.read_point_cloud(r"C:\Users\Administrator\Desktop\bag_test\2023-11-4-9-40-17\merged_cropped_2023-11-04-10-36-52.pcd")
    # pcd = pcd.voxel_down_sample(VOXEL_SIZE)
    # o3d.io.write_point_cloud(r"C:\Users\Administrator\Desktop\test.pcd", pcd)


if __name__ == '__main__':
    main()
