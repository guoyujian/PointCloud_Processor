import open3d as o3d
import open3d.visualization.gui as gui
import open3d.visualization.rendering as rendering
import numpy as np
import copy
from enum import Enum





class App:
    MENU_OPEN = 1

    MENU_SHOW = 5

    MENU_QUIT = 20
    MENU_ABOUT = 21

    show = True

    _picked_indicates = []
    _picked_points = []
    _pick_num = 0

    _label3d_list = []

    def __init__(self):
        gui.Application.instance.initialize()

        self.window = gui.Application.instance.create_window("Pick Points", 800, 600)
        w = self.window
        em = w.theme.font_size

        # 渲染窗口
        self._scene = gui.SceneWidget()
        self._scene.scene = rendering.Open3DScene(w.renderer)
        self._scene.set_on_mouse(self._on_mouse_widget3d)

        self._info = gui.Label("")
        self._info.visible = False

        # 布局回调函数
        w.set_on_layout(self._on_layout)
        w.add_child(self._scene)
        w.add_child(self._info)

        # ---------------Menu----------------
        # 菜单栏是全局的（因为macOS上是全局的）
        # 无论创建多少窗口，菜单栏只创建一次。

        # ----以下只针对Windows的菜单栏创建----
        if gui.Application.instance.menubar is None:
            # 文件菜单栏
            file_menu = gui.Menu()
            file_menu.add_item("Open", App.MENU_OPEN)
            file_menu.add_separator()
            file_menu.add_item("Quit", App.MENU_QUIT)

            # 显示菜单栏
            show_menu = gui.Menu()
            show_menu.add_item("Show Geometry", App.MENU_SHOW)
            show_menu.set_checked(App.MENU_SHOW, True)

            # 帮助菜单栏
            help_menu = gui.Menu()
            help_menu.add_item("About", App.MENU_ABOUT)
            help_menu.set_enabled(App.MENU_ABOUT, False)

            # 菜单栏
            menu = gui.Menu()
            menu.add_menu("File", file_menu)
            menu.add_menu("Show", show_menu)
            menu.add_menu("Help", help_menu)

            gui.Application.instance.menubar = menu

            # -----注册菜单栏事件------
            w.set_on_menu_item_activated(App.MENU_OPEN, self._menu_open)
            w.set_on_menu_item_activated(App.MENU_QUIT, self._menu_quit)
            w.set_on_menu_item_activated(App.MENU_SHOW, self._menu_show)

    # 鼠标事件
    def _on_mouse_widget3d(self, event):
        if event.type == gui.MouseEvent.Type.BUTTON_DOWN and event.is_button_down(
                gui.MouseButton.LEFT) and event.is_modifier_down(gui.KeyModifier.CTRL):

            def depth_callback(depth_image):

                x = event.x - self._scene.frame.x
                y = event.y - self._scene.frame.y

                depth = np.asarray(depth_image)[y, x]

                if depth == 1.0:
                    # 远平面（没有几何体）
                    text = ""
                else:
                    world = self._scene.scene.camera.unproject(x, self._scene.frame.height - y, depth,
                                                               self._scene.frame.width, self._scene.frame.height)

                    text = "({:.3f}, {:.3f}, {:.3f})".format(world[0], world[1], world[2])

                    idx = self._cacl_prefer_indicate(world)
                    true_point = np.asarray(self.pcd.points)[idx]

                    self._pick_num += 1
                    self._picked_indicates.append(idx)
                    self._picked_points.append(true_point)

                    print(f"Pick point #{idx} at ({true_point[0]}, {true_point[1]}, {true_point[2]})")

                def draw_point():
                    self._info.text = text
                    self._info.visible = (text != "")
                    self.window.set_needs_layout()

                    if depth != 1.0:
                        label3d = self._scene.add_3d_label(true_point, "#" + str(self._pick_num))
                        self._label3d_list.append(label3d)

                        # 标记球
                        sphere = o3d.geometry.TriangleMesh.create_sphere(0.0025)
                        sphere.paint_uniform_color([1, 0, 0])
                        sphere.translate(true_point)
                        material = rendering.MaterialRecord()
                        material.shader = 'defaultUnlit'
                        self._scene.scene.add_geometry("sphere" + str(self._pick_num), sphere, material)
                        self._scene.force_redraw()

                gui.Application.instance.post_to_main_thread(self.window, draw_point)

            self._scene.scene.scene.render_to_depth_image(depth_callback)
            return gui.Widget.EventCallbackResult.HANDLED
        elif event.type == gui.MouseEvent.Type.BUTTON_DOWN and event.is_button_down(
                gui.MouseButton.RIGHT) and event.is_modifier_down(gui.KeyModifier.CTRL):
            if self._pick_num > 0:
                idx = self._picked_indicates.pop()
                point = self._picked_points.pop()

                print(f"Undo pick: #{idx} at ({point[0]}, {point[1]}, {point[2]})")

                self._scene.scene.remove_geometry('sphere' + str(self._pick_num))
                self._pick_num -= 1
                self._scene.remove_3d_label(self._label3d_list.pop())
                self._scene.force_redraw()
            else:
                print("Undo no point!")
            return gui.Widget.EventCallbackResult.HANDLED
        return gui.Widget.EventCallbackResult.IGNORED

    def _cacl_prefer_indicate(self, point):


        pcd_tree = o3d.geometry.KDTreeFlann(pcd)
        [k, idx, _] = pcd_tree.search_knn_vector_3d(point, 2)
        return idx[-1]

    # 打开并显示一个obj模型
    def _menu_open(self):
        # 文件拾取对话框
        file_picker = gui.FileDialog(gui.FileDialog.OPEN, "Select file...", self.window.theme)

        # 文件类型过滤
        file_picker.add_filter('.obj', 'obj model files')
        file_picker.add_filter('', 'All files')

        # 初始文件路径
        file_picker.set_path('./model')

        # 设置对话框按钮回调
        file_picker.set_on_cancel(self._on_cancel)
        file_picker.set_on_done(self._on_done)

        # 显示对话框
        self.window.show_dialog(file_picker)

    def _on_cancel(self):
        # 关闭当前对话框
        self.window.close_dialog()

    def _on_done(self, filename):
        self.window.close_dialog()
        self.load(filename)

    def load(self, file):
        # 读取模型文件
        mesh = o3d.io.read_triangle_mesh(file)
        mesh.compute_vertex_normals()
        # 定义材质
        material = rendering.MaterialRecord()
        material.shader = 'defaultLit'

        # 向场景中添加模型
        self._scene.scene.add_geometry('bunny', mesh, material)
        bounds = mesh.get_axis_aligned_bounding_box()
        self._scene.setup_camera(60, bounds, bounds.get_center())

        # 重绘
        self._scene.force_redraw()

        self.mesh = mesh

        self.pcd = o3d.geometry.PointCloud()
        self.pcd.points = o3d.utility.Vector3dVector(np.asarray(mesh.vertices))
        self.pcd.normals = o3d.utility.Vector3dVector(np.asarray(mesh.vertex_normals))

    # 退出应用
    def _menu_quit(self):
        self.window.close()

    # 切换显示模型
    def _menu_show(self):
        self.show = not self.show
        gui.Application.instance.menubar.set_checked(App.MENU_SHOW, self.show)
        self._scene.scene.show_geometry('bunny', self.show)

    def _on_layout(self, layout_context):
        r = self.window.content_rect
        self._scene.frame = r

        pref = self._info.calc_preferred_size(layout_context, gui.Widget.Constraints())
        self._info.frame = gui.Rect(
            r.x, r.get_bottom() - pref.height, pref.width, pref.height)

    def run(self):
        gui.Application.instance.run()


if __name__ == "__main__":
    app = App()
    app.run()
