import open3d as o3d
import open3d.visualization.gui as gui
import open3d.visualization.rendering as rendering


class App:
    MENU_OPEN = 1

    MENU_SHOW = 5

    MENU_QUIT = 20
    MENU_ABOUT = 21

    show = True

    def __init__(self):
        gui.Application.instance.initialize()

        self.window = gui.Application.instance.create_window("layout", 800, 600)
        w = self.window
        em = w.theme.font_size

        # 渲染窗口
        self._scene = gui.SceneWidget()
        self._scene.scene = rendering.Open3DScene(w.renderer)

        # 右侧面板
        self._pannel = gui.CollapsableVert('panel', 0, gui.Margins(0.25 * em, 0.25 * em, 0.25 * em, 0.25 * em))
        for i in range(15):
            self._pannel.add_child(gui.Label(f"{i}-th label"))

        self._button = gui.Button("button")

        # 布局回调函数
        w.set_on_layout(self._on_layout)
        w.add_child(self._scene)
        w.add_child(self._pannel)
        w.add_child(self._button)

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

    # 退出应用
    def _menu_quit(self):
        self.window.close()

    # 切换显示模型
    def _menu_show(self):
        self.show = not self.show
        gui.Application.instance.menubar.set_checked(App.MENU_SHOW, self.show)
        self._scene.scene.show_geometry('bunny', self.show)

    def _on_layout(self, layout_context):
        #   在on_layout回调函数中应正确设置所有子对象的框架(position + size)，
        #   回调结束之后才会布局孙子对象。

        r = self.window.content_rect
        self._scene.frame = r

        pannel_width = 17 * layout_context.theme.font_size
        pannel_height = min(
            r.height, self._pannel.calc_preferred_size(
                layout_context, gui.Widget.Constraints()).height
        )
        self._pannel.frame = gui.Rect(r.get_right() - pannel_width, r.y, pannel_width, pannel_height)

        button_pref = self._button.calc_preferred_size(
            layout_context, gui.Widget.Constraints())
        self._button.frame = gui.Rect(r.x, r.get_bottom() - button_pref.height, button_pref.width, button_pref.height)

    def run(self):
        gui.Application.instance.run()


if __name__ == "__main__":
    app = App()
    app.run()
