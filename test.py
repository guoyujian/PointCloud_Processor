import random

from loguru import logger
import open3d as o3d
from open3d.cpu.pybind.visualization import VisualizerWithEditing
import open3d.visualization.gui as gui
import open3d.visualization.rendering as rendering
from collections import namedtuple
import numpy as np
import rosbag
from merge_pointcloud import SimpleMerge
from utils.math_utils import get_translation_and_rotation_matrix_from
from copy import  deepcopy

color = namedtuple('color', 'name rgb_array')

colors = [
    color(name='赤', rgb_array=[1., 0., 0.]),
    color(name='橙', rgb_array=[1., 0.647, 0.]),
    color(name='黄', rgb_array=[1., 1., 0.]),
    color(name='绿', rgb_array=[0., 1., 0.]),
    color(name='青', rgb_array=[0., 0.498, 1.]),
    color(name='蓝', rgb_array=[0., 0., 1.]),
    color(name='紫', rgb_array=[0.545, 0., 1.]),
]

def show_pcd_with_editing(merged_pcd_filepath: str):
    logger.info('请裁剪点云，并选择需要计算距离的点')

    pcd: o3d.geometry.PointCloud = o3d.io.read_point_cloud(merged_pcd_filepath)
    vis: VisualizerWithEditing = o3d.visualization.VisualizerWithEditing()
    vis.create_window()
    vis.add_geometry(pcd)

    vis.run()  # user edit and picks points
    vis.destroy_window()
    picked_points_index = vis.get_picked_points()
    cropped_pcd = vis.get_cropped_geometry()
    # vis.close()
    show_pcd_and_picked_points(cropped_pcd, picked_points_index)
    # return

def show_pcd_and_picked_points(pcd, points):
    show_pcd = [pcd]
    select_colors_index = random.sample(range(len(colors)), len(points))
    for point_index, color_index in zip(points,select_colors_index):
        xyz = pcd.points[point_index]

        sphere: o3d.geometry.TriangleMesh = o3d.geometry.TriangleMesh.create_sphere(0.2)
        sphere.compute_vertex_normals()
        sphere.translate(xyz)
        sphere.paint_uniform_color(colors[color_index].rgb_array)
        print(f'{colors[color_index].name}色点的坐标为：{xyz}')
        show_pcd.append(sphere)

    o3d.visualization.draw_geometries(show_pcd)


    # o3d_vis = o3d.visualization.VisualizerWithVertexSelection()
    # o3d_vis.create_window()
    # o3d_vis.add_geometry(cropped_pcd)
    #
    # o3d_vis.add_picked_points(o3d.utility.IntVector(picked_points_index))
    #
    # o3d_vis.run()

    # new_pcd = pcd.select_by_index(picked_points_index)
    # sizes = [0.2] * len(picked_points_index)
    # # new_pcd.point_size = o3d.utility.DoubleVector(sizes)
    # o3d.visualization.draw_geometries([pcd], point_size = [20,])
    # o3d.io.write_point_cloud('C:/Users/Administrator/Desktop/cropped.pcd', cropped_pcd)




def key_pcd(pcd1, pcd2, r):
    vis = o3d.visualization.VisualizerWithKeyCallback()

    def key_action_callback(vis: o3d.visualization.Visualizer, action, mods):
        print(action)
        print(mods)
        nonlocal pcd1, r
        if action == 1:  # key down
            print('True')
            vis.remove_geometry(pcd1)
            r = r - 0.1
            pcd1 = o3d.geometry.TriangleMesh.create_sphere(r)
            pcd1.translate([2, 0, 0])
            vis.add_geometry(pcd1)
            return True


        return False

    vis.register_key_action_callback(ord(' '), key_action_callback)  # space
    vis.create_window()
    vis.add_geometry(pcd1)
    vis.add_geometry(pcd2)
    vis.run()
    vis.destroy_window()

def main():
    # 创建点云
    # r = 1
    # pcd1: o3d.geometry.TriangleMesh = o3d.geometry.TriangleMesh.create_sphere(r)
    # pcd1.translate([2,0,0])
    # center = pcd1.get_center()
    # print(center)
    # pcd: o3d.geometry.PointCloud = o3d.io.read_point_cloud(r"C:/Users/Administrator/Desktop/merged_room.pcd")
    # pcd.compute_mahalanobis_distance()
    # # pcd1.get


    # pcd2 = o3d.geometry.TriangleMesh.create_sphere(r)
    # pcd2.translate([0,2,0])
    # key_pcd(pcd1, pcd2, r)
    # pcd1.paint_uniform_color([1,0,0])

    #
    # with rosbag.Bag("C:\\Users\\Administrator\\Desktop\\bag_test1\\2023-11-4-14-10-54.bag", 'r') as bag:
    #     info = bag.get_type_and_topic_info()
    #     print(info.topics)
    #     i = 0
    #     for topic, msg, t in bag.read_messages(topics=['/os_cloud_node/points']):
    #         i+=1
    #         if i > 20:
    #             break
    #         print(f'topic:{topic}; msg: {msg};')
    # 修正坐标后的
    pcd: o3d.geometry.PointCloud = o3d.io.read_point_cloud(r"C:\Users\Administrator\Desktop\bag_test\fp1_2023-11-10-14-20-14\merged_cropped_2023-11-10-16-28-00.pcd")
    # 半径滤波
    num_points = 20  # 邻域球内的最少点数，低于该值的点为噪声点
    radius = 0.05  # 邻域半径大小
    # 执行半径滤波，返回滤波后的点云ror_pcd和对应的索引ind
    ror_pcd, ind = pcd.remove_radius_outlier(num_points, radius)
    ror_pcd.paint_uniform_color([0, 0, 1])
    print("半径滤波后的点云：", ror_pcd)
    # ror_pcd.paint_uniform_color([0, 1, 0])
    # 提取噪声点云
    ror_noise_pcd = pcd.select_by_index(ind, invert=True)


    print("噪声点云：", ror_noise_pcd)
    ror_noise_pcd.paint_uniform_color([1, 0, 1])

    # 可视化滤波结果
    o3d.visualization.draw_geometries([ror_pcd, ror_noise_pcd], window_name="半径滤波",
                                      width=800,  # 窗口宽度
                                      height=600)  # 窗口高度
    o3d.io.write_point_cloud('C:/Users/Administrator/Desktop/test.pcd', ror_pcd)
    # pcd1.remove_statistical_outlier()
    # pcd1.paint_uniform_color([1,0,0])
    # o3d.visualization.draw_geometries_with_editing([pcd1])




    # # 原始点
    # pcd: o3d.geometry.PointCloud = o3d.io.read_point_cloud(
    #     r"C:\Users\Administrator\Desktop\bag_test1\2023-11-4-16-10-10\tmp\1699085419.203.pcd")
    # # c0 = pcd.get_center()
    # pcd_after = deepcopy(pcd)
    # translation_vector, rotation_matrix = (
    #     get_translation_and_rotation_matrix_from(r"C:\Users\Administrator\Desktop\bag_test1\2023-11-4-16-10-10\tmp\1699085419.203.txt"))
    #
    # pcd.rotate(rotation_matrix, center = (0,0,0))
    # pcd.translate(translation_vector)
    #

    # pcd_after.rotate(rotation_matrix, center = (1,0,0))
    # pcd_after.translate(translation_vector)

    #
    # pcd.paint_uniform_color([0,1,0])
    # pcd_after.paint_uniform_color([0, 0, 1])

    # o3d.visualization.draw_geometries([pcd1, pcd_after])
    # o3d.visualization.draw_geometries_with_editing([pcd_after])
    # o3d.visualization.draw_geometries_with_editing([pcd1])
    # o3d.visualization.draw_geometries([pcd1, pcd_after])

    # distances = np.linalg.norm(pcd.points, axis=1)
    # # 根据索引保留点
    # pcd = pcd.select_by_index(
    #     np.where((distances >= 0.7) & (distances <= 70))[0])
    # logger.info(f'修正坐标后的点云数量：{pcd1}；修正坐标前，去掉一定范围外的点云数量：{pcd}')
    #
    # o3d.visualization.draw_geometries([ pcd1, pcd])
    # #
    #
    # o3d.
    # # 计算每个点到坐标原点的L2范数
    # distances = np.linalg.norm(pcd.points, axis=1)
    # # 根据索引保留点
    # pcd = pcd.select_by_index(
    #     np.where((distances >= 0.7) & (distances <= 70))[0])
    # logger.info(f'去掉一定距离外的点云数量：{pcd}')
    # center = pcd.get_center()
    # logger.info(f'修正坐标前的殿云中心: {center}')
    #
    #
    # with open('C:/Users/Administrator/Desktop/l1.txt', 'w') as f:
    #     l = np.asarray(pcd.points).tolist()
    #     f.write(str(l))
    #
    # ddd = pcd1.compute_point_cloud_distance(pcd)
    # # logger.info(f'pcd1 距离pcd{ddd}')
    # points = np.asarray(pcd.points)
    # # sorted_points = np.sort(points)
    #
    #

    # logger.info(f'点云数量：{pcd}; before pcd: {np.asarray(pcd.points)[:10]}')
    # pcd.rotate(rotation_matrix, center = [0,0,0])
    # pcd.translate(translation_vector)
    # logger.info(f'修正坐标前的殿云中心: {pcd.get_center()}')
    # # logger.info(f'pcd1 距离pcd{ddd}')
    # logger.info(f'点云数量：{pcd}; after pcd: {np.asarray(pcd.points)[:10]}')





    # o3d.visualization.draw_geometries([pcd])
    # translation_vector, rotation_matrix = SimpleMerge('', '').get_translation_and_rotation_matrix_from(r"C:\work\point_cloud\bag-files\2023-11-4-16-10-10\1699085412.003.txt")
    # logger.info(f'trans: {translation_vector}; rotate: {rotation_matrix}')
    # pcd.rotate(rotation_matrix, center = np.array([0.,0.,0.]))
    # pcd.translate(translation_vector)
    # # pcd.has_points()
    # l = np.asarray(pcd.points).tolist()
    # with open('C:/Users/Administrator/Desktop/l.txt', 'w') as f:
    #     f.write(str(l))
    # pcd1: o3d.geometry.PointCloud = o3d.io.read_point_cloud(r"C:\Users\Administrator\Desktop\bag_test\data_2023-11-06-12-07-36\tmp\1699085412.003.pcd")
    # # pcd1: o3d.geometry.PointCloud = o3d.io.read_point_cloud(r"C:\work\point_cloud\bag-files\2023-11-4-16-10-10\1699085412.003.pcd")
    #
    # l1 = np.asarray(pcd1.points).tolist()
    # # l1.tofile('C:/Users/Administrator/Desktop/l1.txt')
    # with open('C:/Users/Administrator/Desktop/l1.txt', 'w') as f:
    #     f.write(str(l1))
    # logger.info(f'{np.asarray(pcd1.points)}')
    #
    # v1, m1 = SimpleMerge('', '').get_translation_and_rotation_matrix_from(r"C:\Users\Administrator\Desktop\bag_test1\2023-11-4-16-10-10\tmp\1699085428.103.txt")
    # m1:np.ndarray
    #
    # print(v1)
    # print(m1)
    # print(m1.T)





if __name__ == '__main__':
    main()
    # show_pcd_with_editing("C:\\Users\\Administrator\\Desktop\\merged_room.pcd")
    # pcd = o3d.io.read_point_cloud(r"C:\Users\Administrator\Desktop\cropped.pcd")
    # o3d.visualization.draw_geometries([pcd], points)
    # gui.Application.instance.initialize()
    # window = gui.Application.instance.create_window("Mesh-Viewer", 1024, 750)
    #
    # scene = gui.SceneWidget()
    # scene.scene = rendering.Open3DScene(window.renderer)
    # # scene1 = gui.SceneWidget()
    # # scene1.scene = rendering.Open3DScene(window.renderer)
    # window.add_child(scene)
    # # window.add_child(scene1)
    #
    # # mesh = o3d.io.read_triangle_mesh('path/to/data', print_progress=True)
    # mesh = cropped_pcd
    # record = rendering.MaterialRecord()
    # record.shader = 'normals'
    # scene.scene.add_geometry("mesh_name", mesh, record)
    #
    # bounds = mesh.get_axis_aligned_bounding_box()
    # scene.setup_camera(60, bounds, bounds.get_center())
    #
    #
    # for index in picked_points_index:
    #     coordinate =cropped_pcd.points[index]
    #     logger.info(coordinate)
    #     scene.add_3d_label(coordinate, f"A")
    #
    # gui.Application.instance.run()  # Run until user closes window






    # 创建可视化窗口并绘制点云
    # o3d.visualization.draw_geometries([pcd1])

