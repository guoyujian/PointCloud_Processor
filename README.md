# 简介
该项目基于open3d-python处理点云数据
# 标准流程
1. 扫描得到bag文件
2. 将得到的所有bag文件放在一个干净的目录下
3. 执行`python bag2pcd_one_stop_service.py <bag_dir>`
   1. 该脚本会生成一个目录tmp用于存放从bag包解析出的所有pcd文件和里程计信息；
   2. 该脚本会并将所有pcd文件拼接为一个完整的pcd点云文件
4. 执行`python edit_pcd_and_pick_points_and_compute_distance_script.py`
   1. 输入上一步得到的pcd文件的路径
   2. 裁剪点云
   3. 如果需要，选择若干点进行点点之间距离计算
   4. 关闭窗口，按任意键程序打开新的窗口，调整视角和选中点的大小
   5. 再次关闭窗口将自动保存当前视角的截图、裁剪后的点云文件以及点点之间的距离
5. 执行`python calculate_distance_between_centers_of_2_pointclouds_script.py`
   1. 输入两个裁剪后的pcd文件路径
   2. 程序分别计算两个点云的质心，并在窗口中展示
   3. 用户调整质心位置，关闭窗口将自动保存当前视角下的截图并计算质心之间的欧式距离
6.  执行`python compute_convex_hull_volume.py`，输入裁剪后的pcd文件路径；程序将计算凸包体积并保存凸包截图
