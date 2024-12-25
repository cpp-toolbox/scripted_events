bl_info = {
    "name": "Export Timeline Markers",
    "blender": (3, 0, 0),
    "category": "Timeline",
    "author": "cuppajoeman",
    "description": "Exports all timeline markers to a text file with their time and names."
}

import bpy
import os

class EXPORT_OT_timeline_markers(bpy.types.Operator):
    """
    Operator to export timeline markers to a text file
    """
    bl_idname = "export.timeline_markers"
    bl_label = "Export Timeline Markers"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: bpy.props.StringProperty(
        name="File Path",
        description="File path to save the marker data",
        subtype='FILE_PATH'
    )

    def execute(self, context):
        markers = context.scene.timeline_markers

        if not markers:
            self.report({'WARNING'}, "No markers found in the timeline.")
            return {'CANCELLED'}

        try:
            with open(self.filepath, 'w') as file:
                file.write("Time (s)\tMarker Name\n")
                for marker in markers:
                    time_in_seconds = marker.frame / context.scene.render.fps
                    file.write(f"{time_in_seconds:.2f}\t{marker.name}\n")

            self.report({'INFO'}, f"Markers exported to {self.filepath}")
            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Failed to write to file: {e}")
            return {'CANCELLED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

# Register and unregister classes
def menu_func(self, context):
    self.layout.operator(EXPORT_OT_timeline_markers.bl_idname)

def register():
    bpy.utils.register_class(EXPORT_OT_timeline_markers)
    bpy.types.TOPBAR_MT_file_export.append(menu_func)

def unregister():
    bpy.utils.unregister_class(EXPORT_OT_timeline_markers)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func)

if __name__ == "__main__":
    register()
