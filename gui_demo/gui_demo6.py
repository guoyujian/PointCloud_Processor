import open3d as o3d
import open3d.visualization.gui as gui
import open3d.visualization.rendering as rendering
import numpy as np


class App:

    _picked_indicates = []
    _picked_positions = []
    _picked_num = 0
    _picked_label3d = []

    mesh = None
    mesh_wireframe = None
    mesh_kdtree = None

    def __init__(self) -> None:
        gui.Application.instance.initialize()
        self.window = gui.Application.instance.create_window(
            "Pick Points", 800, 600)

        self._scene3d = gui.SceneWidget()
        self._scene3d.scene = rendering.Open3DScene(self.window.renderer)
        self._scene3d.set_on_mouse(self._mouse_event)

        self.window.add_child(self._scene3d)

        self.mesh = o3d.geometry.TriangleMesh.create_sphere()
        self.mesh_kdtree = o3d.geometry.KDTreeFlann(self.mesh)
        self.mesh_wireframe = o3d.geometry.LineSet.create_from_triangle_mesh(
            self.mesh)
        self.mesh_wireframe.paint_uniform_color([.7, .7, .7])
        self._scene3d.scene.add_geometry(
            "geometry", self.mesh, rendering.MaterialRecord())
        wireframe_material = rendering.MaterialRecord()
        wireframe_material.shader = 'unlitLine'
        self._scene3d.scene.add_geometry(
            "wireframe", self.mesh_wireframe, wireframe_material)
        bounds = self.mesh.get_axis_aligned_bounding_box()
        self._scene3d.setup_camera(60, bounds, bounds.get_center())

    def _mouse_event(self, event):
        if event.type == gui.MouseEvent.Type.BUTTON_DOWN and event.is_button_down(gui.MouseButton.LEFT) and event.is_modifier_down(gui.KeyModifier.CTRL):

            def depth_callback(depth_image):
                x = event.x - self._scene3d.frame.x
                y = event.y - self._scene3d.frame.y

                depth = np.asarray(depth_image)[y, x]

                if depth == 1.0:
                    return
                else:
                    world_coord = self._scene3d.scene.camera.unproject(
                        x, y, depth, self._scene3d.frame.width, self._scene3d.frame.height)
                    idx = self._calc_prefer_indicate(world_coord)
                    picked_point = np.asarray(self.mesh.vertices)[idx]

                    self._picked_num += 1
                    self._picked_indicates.append(idx)
                    self._picked_positions.append(picked_point)

                    print(
                        f"Picked point #{idx} at ({picked_point[0]}, {picked_point[1]}, {picked_point[2]})")

                    def draw_point():
                        label3d = self._scene3d.add_3d_label(
                            picked_point, "#"+str(self._picked_num))
                        self._picked_label3d.append(label3d)

                        sphere = o3d.geometry.TriangleMesh.create_sphere(
                            0.025)
                        sphere.paint_uniform_color([1, 0, 0])
                        sphere.translate(picked_point)
                        material = rendering.MaterialRecord()
                        material.shader = 'defaultUnlit'

                        self._scene3d.scene.add_geometry(
                            "sphere"+str(self._picked_num), sphere, material)
                        self._scene3d.force_redraw()

                    gui.Application.instance.post_to_main_thread(
                        self.window, draw_point)

            self._scene3d.scene.scene.render_to_depth_image(depth_callback)
            return gui.Widget.EventCallbackResult.HANDLED
        elif event.type == gui.MouseEvent.Type.BUTTON_DOWN and event.is_button_down(gui.MouseButton.RIGHT) and event.is_modifier_down(gui.KeyModifier.CTRL):
            if self._picked_num > 0:
                idx = self._picked_indicates.pop()
                point = self._picked_positions.pop()

                print(
                    f"Undo pick: #{idx} at ({point[0]}, {point[1]}, {point[2]})")

                self._scene3d.scene.remove_geometry(
                    'sphere'+str(self._picked_num))
                self._picked_num -= 1
                self._scene3d.remove_3d_label(self._picked_label3d.pop())
                self._scene3d.force_redraw()
            else:
                print('Undo nothing!')
            return gui.Widget.EventCallbackResult.HANDLED
        return gui.Widget.EventCallbackResult.IGNORED

    def _calc_prefer_indicate(self, point):
        [k, idx, _] = self.mesh_kdtree.search_knn_vector_3d(point, 1)
        return idx[0]

    def run(self):
        gui.Application.instance.run()


if __name__ == '__main__':
    app = App()
    app.run()