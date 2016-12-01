# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****

bl_info = {
    "name": "Cutaway Shader",
    "author": "Dylan Whiteman",
    "version": (1, 0),
    "blender": (2, 77, 0),
    "location": "Shader Node > Add > Effect Shaders > Cutaway Shader",
    "description": "Cut away the parts of an object (or selected objects) that are in front of the 'Cutaway Plane'",
    "warning": "Alpha Release (save your work before using!)",
    "wiki_url": "",
    "category": "Node"}
    
import bpy
from bpy.types import NodeTree, Node, NodeSocket
import string
import bmesh
import mathutils
import os
from bpy_extras.image_utils import load_image


# *************************************************************************************
# *************************************************************************************
#
# Operators (buttons and menus) called by the py node 
#
# *************************************************************************************
# *************************************************************************************


# < Enable OSL Button >
class casBtnEnableOSL(bpy.types.Operator):
    bl_idname = "cas_btn.enable_osl"
    bl_label = "Enable CPU + OSL Render"
    bl_description = "Enable OSL and GPU rendering. The material will render as black if OSL and CPU rendering are not enabled."
    
    # The enable CPU + OSL Render button has been pressed
    def execute(self, context):
        bpy.context.scene.cycles.shading_system = True
        bpy.context.scene.cycles.device = 'CPU'
        ob = bpy.context.scene.objects.active
        if (ob != None):
            # a hack to get the 3D rendered scene to update after choosing a new cutaway plane
            ob.select = True
            ob.delta_location=(0.0, 0.0, 0.0)
        return{'FINISHED'} 
     
    # Check to see if we should be displayed
    @classmethod
    def poll(self, context):
        return True
# < !Enable OSL Button >


# < Add Cutaway Plane Button >
class casBtnAddCutawayPlane(bpy.types.Operator):
    bl_idname = "cas_btn.add_cutawayplane"
    bl_label = "Add New Cutaway Plane"
    bl_description = "Add a Cutaway Plane to the Scene. Objects on the green side of the plane are 'go' for cutting away. Objects on the red side of the plane will not be cut away. The Cutaway Plane is invisible in the preview and final renders."
    
    # A link back to the setup node that this button sits in (there may be more that 1 setup node in the tree)
    setupnode_namestr2 = bpy.props.StringProperty(name="")      # passed to us as a keyword argument on creation
      
    # The add cutaway plane button has been pressed
    def execute(self, context):
        # Get a reference to the parent node where the button was pressed  
        node_tree = context.space_data.edit_tree
        nodes = node_tree.nodes
        py_node = nodes[self.setupnode_namestr2]
          
        # Create a helper red/green material to add to the new cutaway plane  
        # (objects on the green side are 'go' for being cutaway. 
        # Objects on the red side are not allowed to be cut away.     
        mat = py_node.create_cutawayplane_material()
        
        # tell the parent node to add a new cutaway plane mesh with the given red/green helper material
        py_node.addNewCutawayPlane(context,mat)
        return{'FINISHED'} 
     
    # Check to see if we should be displayed
    @classmethod
    def poll(self, context):
        return True
# < !Add Cutaway Plane Button >

# < Shows the Load image file dialog and returns the filepath to the selection or "">
class casBtnOpenImageDialog(bpy.types.Operator):
    bl_idname = "cas_btn.open_image_dialog"
    bl_label = "Load Image"
    bl_description = "Open Image File"

    setupnode_namestr_iai = bpy.props.StringProperty()
    filepath = bpy.props.StringProperty(subtype="FILE_PATH")
    #filter_glob = bpy.props.StringProperty( default="*.png;*.jpg;*.dds;*.gif", options={'HIDDEN'})
    filter_image = bpy.props.BoolProperty(default=True, options={'HIDDEN', 'SKIP_SAVE'})
    filter_folder = bpy.props.BoolProperty(default=True, options={'HIDDEN', 'SKIP_SAVE'})
    filter_glob = bpy.props.StringProperty(default="", options={'HIDDEN', 'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):
        # Get a reference to the parent node where the button whas pressed  
        node_tree = context.space_data.edit_tree
        nodes = node_tree.nodes
        py_node = nodes[self.setupnode_namestr_iai]
          

        
        # tell the parent node open the selected image and use it to define the cutaway shape
        py_node.open_image_dialog(self.filepath)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
# < !Shows the Load image file dialog and returns the filepath to the selection or "">


# < Add ChildNodes to Selected Objects>
# select all objects in the scene that are a child of the parent node
class casBtnAddChildNodesToSelected(bpy.types.Operator):
    bl_idname = "cas_btn.add_child_nodes_to_selected"
    bl_label = "Add ChildNodes to Selected"
    bl_description = "Add 'child' cutaway shaders to selected objects materials. Child shaders inherit all the settings from this parent shader (e.g.  Effect Mix, Cutaway Plane Selection etc ...)"
    
    # A link back to the setup node that this button sits in (there may be more that 1 setup node in the tree)
    setupnode_namestr_asts = bpy.props.StringProperty(name="")      # passed to us as a keyword argument on creation
      
    # The add cutaway plane button has been pressed
    def execute(self, context):
        # Get a reference to the parent node where the button whas pressed  
        node_tree = context.space_data.edit_tree
        nodes = node_tree.nodes
        py_node = nodes[self.setupnode_namestr_asts]
          
        # tell the parent node to select all ChildNodes in the scene
        py_node.add_child_nodes_to_selected()
        return{'FINISHED'} 
     
    # Check to see if we should be displayed
    @classmethod
    def poll(self, context):
        return True
# < !Add ChildNodes to Selected >


# < Remove ChildNodes from Selected Objects>
# select all objects in the scene that are a child of the parent node
class casBtnRemoveChildNodesFromSelected(bpy.types.Operator):
    bl_idname = "cas_btn.remove_child_nodes_from_selected"
    bl_label = "Remove ChildNodes from Selected"
    bl_description = "Remove this parents child shaders from the materials of the selected objects."
    
    # A link back to the setup node that this button sits in (there may be more that 1 setup node in the tree)
    setupnode_namestr_rsfs = bpy.props.StringProperty(name="")      # passed to us as a keyword argument on creation
      
    # The add cutaway plane button has been pressed
    def execute(self, context):
        # Get a reference to the parent node where the button whas pressed  
        node_tree = context.space_data.edit_tree
        nodes = node_tree.nodes
        py_node = nodes[self.setupnode_namestr_rsfs]
          
        # tell the parent node to select all ChildNodes in the scene
        py_node.remove_child_nodes_from_selected()
        return{'FINISHED'} 
     
    # Check to see if we should be displayed
    @classmethod
    def poll(self, context):
        return True
# < !Remove ChildNodes from Selected Objects >



# < Select All ChildNodes Button >
# select all objects in the scene that are a child of the parent node
class casBtnSelectAllChildNodes(bpy.types.Operator):
    bl_idname = "cas_btn.select_all_child_nodes"
    bl_label = "Select All ChildNodes"
    bl_description = "Select all child objects that use this shader. TIP: Use the Outliner in 'Selected' mode to list all selected objects."
    
    # A link back to the setup node that this button sits in (there may be more that 1 setup node in the tree)
    setupnode_namestr_sas = bpy.props.StringProperty(name="")      # passed to us as a keyword argument on creation
      
    # The add cutaway plane button has been pressed
    def execute(self, context):
        # Get a reference to the parent node where the button whas pressed  
        node_tree = context.space_data.edit_tree
        nodes = node_tree.nodes
        py_node = nodes[self.setupnode_namestr_sas]
          
        # tell the parent node to select all ChildNodes in the scene
        py_node.select_all_child_nodes()
        return{'FINISHED'} 
     
    # Check to see if we should be displayed
    @classmethod
    def poll(self, context):
        return True
# < !Select All ChildNodes Button >


# < Select All Parents Button >
# select all objects in the scene that are a child of the parent node
class casBtnSelectAllParents(bpy.types.Operator):
    bl_idname = "cas_btn.select_all_objects_using_this_parent_node"
    bl_label = "Select All Parents"
    bl_description = "Select all parent objects that use this shader. TIP: Use the Outliner in 'Selected' mode to list all selected objects."
    
    # A link back to the setup node that this button sits in (there may be more that 1 setup node in the tree)
    setupnode_namestr_sap = bpy.props.StringProperty(name="")      # passed to us as a keyword argument on creation
      
    # The add cutaway plane button has been pressed
    def execute(self, context):
        # Get a reference to the parent node where the button whas pressed  
        node_tree = context.space_data.edit_tree
        nodes = node_tree.nodes
        py_node = nodes[self.setupnode_namestr_sap]
          
        # tell the parent node to select all parent objects in the scene that use this node
        py_node.select_all_objects_using_this_parent_node()
        return{'FINISHED'} 
     
    # Check to see if we should be displayed
    @classmethod
    def poll(self, context):
        return True
# < !Select All Parents Button >


# < Select All Parents in Scene Button >
# select all objects in the scene that are a child of the parent node
class casBtnSelectAllParentsInScene(bpy.types.Operator):
    bl_idname = "cas_btn.select_all_parents_in_scene"
    bl_label = "Select All Parents"
    bl_description = "Select all objects in the scene that use a parent Cutaway Shader. TIP: Use the Outliner in 'Selected' mode to list all selected objects."
    
    # A link back to the setup node that this button sits in (there may be more that 1 setup node in the tree)
    setupnode_namestr_sapis = bpy.props.StringProperty(name="")      # passed to us as a keyword argument on creation
      
    # The add cutaway plane button has been pressed
    def execute(self, context):
        # Get a reference to the parent node where the button was pressed  
        node_tree = context.space_data.edit_tree
        nodes = node_tree.nodes
        py_node = nodes[self.setupnode_namestr_sapis]
          
        # tell the parent node to select all parent objects in the scene that use this node
        py_node.select_all_parents_in_scene()   
        return{'FINISHED'} 
     
    # Check to see if we should be displayed
    @classmethod
    def poll(self, context):
        return True
# < !Select All Parents in Scene Button >

# < Remove All Cutaway Shader Nodes from Scene Button >
# Removes all the parent and child cutaway Shader py nodes and thier OSL nodes
class casBtnRemoveAllCutAwayShaderNodes(bpy.types.Operator):
    bl_idname = "cas_btn.remove_all_cut_away_shader_nodes"
    bl_label = "Remove all CutAway Shader Parent and Child Nodes"
    bl_description = "Remove all CutAway Shader Parent and Child Nodes from Scene Materials: Use with caution."
    
    # A link back to the setup node that this button sits in (there may be more that 1 setup node in the tree)
    setupnode_namestr_racsn = bpy.props.StringProperty(name="")      # passed to us as a keyword argument on creation
      
    # The add cutaway plane button has been pressed
    def execute(self, context):
        # Get a reference to the parent node where the button whas pressed  
        node_tree = context.space_data.edit_tree
        nodes = node_tree.nodes
        py_node = nodes[self.setupnode_namestr_racsn]
          
        # tell the parent node to select all parent objects in the scene that use this node
        py_node.remove_all_cut_away_shader_nodes()   
        return{'FINISHED'} 
     
    # Check to see if we should be displayed
    @classmethod
    def poll(self, context):
        return True
# < !Select All Parents in Scene Button >



# < Add Inner Solidify Mesh And Material Button >
class casBtnAddInnerSolidifyMeshAndMaterial(bpy.types.Operator):
    bl_idname = "cas_btn.add_inner_solidifier_mesh_and_material"
    bl_label = "Add child Material"
    bl_description = "A quick way to add thickness (and an optional shaded rim) to the selected object. A Solidify Modifier is automatically added, along with an 'inner mesh' material. Note: The selected object must be using this shader as one of its materials."
    
    # A link back to the setup node that this button sits in (there may be more that 1 setup node in the tree)
    setupnode_namestr_aismam = bpy.props.StringProperty(name="")      # passed to us as a keyword argument on creation
      
    # Buttons execute method. 
    def execute(self, context):
        # get a reference to this buttons pynode
        node_tree = context.space_data.edit_tree
        nodes = node_tree.nodes
        py_node = nodes[self.setupnode_namestr_aismam] 
        # tell the pynode to add a mesh modifier and inner mesh material to the active object
        py_node.add_inner_solidifier_mesh_and_material()      
        return{'FINISHED'} 
     
    # Check to see if we should be displayed
    @classmethod
    def poll(self, context):
        return True
# < !Add child Material Button >


# < Select Cutaway Plane button routines >
# Select Cutaway Plane dynamic drop menu
# Draw the drop down menu. 
#   - The execute function (if the user selects an item) is: cas_menu_select_callback_function
#   - cas_menu_select_callback_function was dynamically defined and registered earlier by the method CasDynamicallyCreateMenuCallBackFunctionForSelectPlane
# List all the (pre-filtered) objects in the scene.
# The menu item selected ny the user becomes the 
# cutaway plane for this node.    
class CasDynamicallyPopulateMenuForSelectPlane(bpy.types.Menu):
    bl_idname = "cas_menu_populate.select_plane"
    bl_label = "Select"
    
    
    menu_prop = bpy.props.StringProperty(name="String Value")
    
    # Draw all the menu items
    def draw(self, context):
        layout = self.layout
        
        call_back_name_str = "cas_menu_dynamic_callback.select_plane"
        filter_str = 'cutaway'
        j = 0
        for i, obj in enumerate(bpy.context.scene.objects): # iterate over all objects in the scene
            if (obj.type == 'MESH'):                        # only process mesh objects
                if  filter_str in obj.name.lower():         # only process mesh objects with the filter_str in their name 
                    cas_menu_select_callback_function = call_back_name_str + str(j)
                    layout.operator(cas_menu_select_callback_function, text=obj.name) 
                    j += 1

# A function to programatically create a menu callback class. .
# The class 'template' we want to create is embedded in this function.
# A new class is re-created and registered for every menu item callback. 
# The only difference between each class is the bl_idname.
def CasDynamicallyCreateMenuCallBackFunctionForSelectPlane(blidstr, blnamestr, setupnode_name_str):
    # This is the class 'template' we want to programatically create
    # bl_idname and bl_label are modified, creating a unique class.
    class menuCallBackTemplate(bpy.types.Operator):
        bl_idname = "cas_menu_dynamic_callback.select_plane" + blidstr
        bl_label = blnamestr
        
        indexProp = bpy.props.FloatProperty(name="A float")
        
        def execute(self, context):
            selectedSplitStr = self.bl_idname.split('_')
            selected = selectedSplitStr[len(selectedSplitStr)-1]
            
            node_tree = context.space_data.edit_tree
            nodes = node_tree.nodes
            py_node = nodes[setupnode_name_str]          #'Cutaway Shader']

            py_node.setNewCutawayPlane(self.bl_label)
            return{'FINISHED'}
        
    # return a reference to the newly created class
    return menuCallBackTemplate

# Select cutaway plane button
# When the user presses this button, a dropdown menu appears with a list of all (filtered) scene objects.
# The menu item selected by the user becomes the cutaway plane for this node.  
class casBtnSelectCutawayPlane(bpy.types.Operator):
    bl_idname = "cas_btn.select_cutaway_plane"
    bl_label = "Select Cutaway Plane Object"
    bl_description = "Select the Cutaway Plane for this shader."
    
    # A link back to the setup node that this button sits in (there may be more that 1 setup node in the tree)
    setupnode_namestr = bpy.props.StringProperty(name="")                  # passed to us as a keyword argument on creation
    
    # Used to filter out unwanted objects in the popup menu. There maybe 1000's of objects in a scene)
    filter_str= bpy.props.StringProperty(name="String Value")
     
    # Create a callback class for each potential popup menu item that the user may select.
    # The popup menu contains all the mesh objects that the user could select to be the cutaway plane.
    def createPopMenuCallbackClasses(self):
        ob_names_str = ""
        filter_str = 'cutaway'
        id = 0
        for i, obj in enumerate(bpy.context.scene.objects): # iterate over all objects in the scene
            if (obj.type == 'MESH'):                        # only process mesh objects
                if  filter_str in obj.name.lower():         # only process mesh objects with the filter_str in their name 
                    # create and regiter each menu items callback class
                    popmenu_callback_class_ref = CasDynamicallyCreateMenuCallBackFunctionForSelectPlane(str(id), obj.name, self.setupnode_namestr) 
                    bpy.utils.register_class(popmenu_callback_class_ref)
                    id +=1  
        # create one last 'callback' class to delineate the end of the sequence.             
        #popmenu_callback_class_ref = self.CasDynamicallyCreateMenuCallBackFunctionForSelectPlane("menu_end", "menu_end") 
        #bpy.utils.register_class(popmenu_callback_class_ref) 
    
    
    # Buttons execute method. Show a drop down menu of all (filtered) objects in the scene
    # xxx todo: look at api prop_search as a method to populate the allowed options. n x
    def execute(self, context):
        # we create the callback classes for each possible menu item selection here
        # because we can't register classes in the CasDynamicallyPopulateMenuForSelectPlane draw() method
        self.createPopMenuCallbackClasses()
        bpy.ops.wm.call_menu(name="cas_menu_populate.select_plane") 
        return{'FINISHED'}  
   
     # Check to see if we should be displayed
    @classmethod
    def poll(self, context):
        return True
# < !Select Cutaway Plane button routines >
         
# < Refresh Cutaway plane (after vertex edit)  Button >
class cas_btn_refresh_cutaway_plane(bpy.types.Operator):
    bl_idname = "cas_btn.refresh_cutaway_plane"
    bl_label = "Refresh"
    bl_description = "Refresh this parent shader (and any child shaders) after cutaway plane vertex edits. (Note: The plane is currently limited to around 50 vertices)."
    # A link back to the setup node that this button sits in (there may be more that 1 setup node in the tree)
    setupnode_namestr_rcp = bpy.props.StringProperty(name="")      # passed to us as a keyword argument on creation
      
    # Buttons execute method. 
    def execute(self, context):
        # get a reference to this buttons pynode
        node_tree = context.space_data.edit_tree
        nodes = node_tree.nodes
        py_node = nodes[self.setupnode_namestr_rcp] 
        # tell the pynode to add a mesh modifier and inner mesh material to the active object
        py_node.refresh_cutaway_plane()      
        return{'FINISHED'} 
     
    # Check to see if we should be displayed
    @classmethod
    def poll(self, context):
        return True
# < !Refresh Cutaway plane (after vertex edit)  Button >

# < Auto Refresh Child nodes with parents keyframed data (if any) (after key frame change )  Button >
class cas_btn_auto_refresh_child_nodes_after_frame_change(bpy.types.Operator):
    bl_idname = "cas_btn.auto_refresh_child_nodes_after_frame_change"
    bl_label = "Auto Refresh"
    bl_description = "Key frame data automatically is copied to child shader nodes when the frame changes during 3D Viewport rendered previews. Unchecked can be faster in big scenes."
    # A link back to the setup node that this button sits in (there may be more that 1 setup node in the tree)
    setupnode_namestr_arcnafc = bpy.props.StringProperty(name="")      # passed to us as a keyword argument on creation
      
    # Buttons execute method. 
    def execute(self, context):
        # get a reference to this buttons pynode
        node_tree = context.space_data.edit_tree
        nodes = node_tree.nodes
        py_node = nodes[self.setupnode_namestr_arcnafc]
        
        #invert the refresh status, add or remove the callback for the refresh.
        refresh_bool = py_node.get_global_auto_update_child_nodes_on_frame_change_bool_create_if_neccessary()
        refresh_bool = not refresh_bool
        py_node.set_global_auto_update_child_nodes_on_frame_change_bool_create_if_neccessary(refresh_bool)
        py_node.manual_refresh_child_nodes_after_frame_change()
        return{'FINISHED'} 
     
    # Check to see if we should be displayed
    @classmethod
    def poll(self, context):
        return True
# < !Auto Refresh Child nodes with parents keyframed data (if any) (after key frame change )  Button >

# < Refresh Cutaway plane (after key frame change )  Button >
# some times the change is not picked up by the pre-frame change routine
# needs further investigation.
class cas_btn_manual_refresh_child_nodes_after_frame_change(bpy.types.Operator):
    bl_idname = "cas_btn.manual_refresh_child_nodes_after_frame_change"
    bl_label = "Refresh"
    bl_description = "Manually refresh keyframed settings to the child shaders."
    # A link back to the setup node that this button sits in (there may be more that 1 setup node in the tree)
    setupnode_namestr_mrcnafc = bpy.props.StringProperty(name="")      # passed to us as a keyword argument on creation
      
    # Buttons execute method. 
    def execute(self, context):
        '''
         # iterate over all materials. For parent pynodes - copy any key framed data to the parent osl shader and child osl shaders
         # this is the same routine as xxx - except the update of values to child nodes is forced.
        for mat in bpy.data.materials:
            if mat.use_nodes:
                for node in mat.node_tree.nodes:
                    if "Cutaway Shader" in node.name:
                    #if node.name.find("Cutaway Shader") != -1:
                        if node.node_is_parent == True:
                            #if (node.effectmix_float_last_frame_value != node.effectmix_float):
                            print("Refresh:Setting effectmix_float for: " + node.name)
                            node.effectmix_float = node.effectmix_float           # setting the property to itself will call the update call back for this property => update this and all child node => update all OSL inputs
                            node.rimeffectmix_float = node.rimeffectmix_float
                            node.edge_fade_distance_float_prop = node.edge_fade_distance_float_prop  
                            node.edge_fade_sharpness_float_prop = node.edge_fade_sharpness_float_prop
        
        '''
        
        # get a reference to this buttons pynode
        node_tree = context.space_data.edit_tree
        nodes = node_tree.nodes
        py_node = nodes[self.setupnode_namestr_mrcnafc] 
        py_node.manual_refresh_child_nodes_after_frame_change()     
        return{'FINISHED'} 
     
    # Check to see if we should be displayed
    @classmethod
    def poll(self, context):
        return True
# < !Refresh Cutaway plane (after vertex edit)  Button >



'''
# < Select child Cutaway Shader button routines >
# Select child Cutaway Shader Node drop menu
# Draw the drop down menu. 
#   - The execute function (if the user selects an item) is: cas_menu_select_callback_function
#   - cas_menu_select_callback_function was dynamically defined and registered earlier by the method CasDynamicallyCreateMenuCallBackFunctionForSelectPlane
# 
# List all the (pre-filtered) objects in the scene.
# The menu item selected ny the user becomes the 
# cutaway plane for this node.    
class CasDynamicallyPopulateMenuForSelectchildNode(bpy.types.Menu):
    bl_idname = "cas_menu_populate.select_child_node"
    bl_label = "Select child Cutaway Shader"
    
    menu_prop = bpy.props.StringProperty(name="String Value")
    
    # Draw all the menu items
    def draw(self, context):
        layout = self.layout
        j = 0
        call_back_name_str = "cas_menu_dynamic_callback.select_child_node"
        
        # node need to filter our own name out
        for i, mat in enumerate(bpy.context.blend_data.materials):  # iterate over all materials in the scene
            if (mat.use_nodes):
                for node in mat.node_tree.nodes:
                    if ("Cutaway Shader" in node.name):
                        if (node.node_is_parent and (node.child_node_name_str == '')):
                            cas_menu_select_callback_function = call_back_name_str + str(j)
                            layout.operator(cas_menu_select_callback_function, 'Mat: ' + mat.name + ' : ' + node.name) 
                            j += 1
        cas_menu_select_callback_function = call_back_name_str + str(j)
        layout.operator(cas_menu_select_callback_function, 'SELECT NONE') 


# A function to programaticaly create a menu callback class. .
# The class 'template' we want to create is embedded in this function.
# A new class is re-created and registered for every menu item callback. 
# The only difference between each class is the bl_idname.
def CasDynamicallyCreateMenuCallBackFunctionForSelectchildNode(blidstr, blnamestr, setupnode_name_str):
    # This is the class 'template' we want to programatically create
    # bl_idname and bl_label are modified, creating a unique class.
    class menuCallBackTemplate(bpy.types.Operator):
        bl_idname = "cas_menu_dynamic_callback.select_child_node" + blidstr
        bl_label = blnamestr
        
        indexProp = bpy.props.FloatProperty(name="A float")
        
        def execute(self, context):
            selectedSplitStr = self.bl_idname.split('_')
            selected = selectedSplitStr[len(selectedSplitStr)-1]
            
            node_tree = context.space_data.edit_tree
            nodes = node_tree.nodes
            py_node = nodes[setupnode_name_str]    

            py_node.setNewchildNode(self.bl_label)
            return{'FINISHED'}
        
    # return a reference to the newly created class
    return menuCallBackTemplate
   

# When the user presses this button, a dropdown menu appears with a list of all materials in the scene.
# The menu item selected by the user becomes the child material that contains the child cutaway shader node.
# The child cutaway shader node has all the settings of the parent cut away shader node (e.g. the current
# cut away plane etc) copied to it. This feature is useful when a Thickness Modifier has been applied to an 
# 'outer' mesh because 'inner' mesh (created by the thickness modifier)  also needs to be cut away. 
class casBtnSelectchildLinkMaterial(bpy.types.Operator):
    bl_idname = "cas_btn.select_child_shader"
    bl_label = "Select child Cutaway Shader Node" # test
    
    # A link back to the setup node that this button sits in (there may be more that 1 setup node in the tree)
    # passed to us as a keyword argument on creation
    setupnode_namestr = bpy.props.StringProperty(name="")                  
    
    # Used to filter out unwanted objects in the popup menu. There maybe 1000's of objects in a scene)
    filter_str= bpy.props.StringProperty(name="String Value")
     
    # Create a callback class for each potential popup menu item that the user may select.
    # The popup menu contains all the mesh objects that the user could select to be the cutaway plane.
    def createPopMenuCallbackClasses(self):
        id = 0
        for i, mat in enumerate(bpy.context.blend_data.materials):              # iterate over all materials in the scene
            if (mat.use_nodes):
                for node in mat.node_tree.nodes:
                    if ("Cutaway Shader" in node.name):                         #if ((node.name != None) and ("Cutaway Shader" in node.name)):
                        if (node.node_is_parent and (node.child_node_name_str == '')):
                            # create and regiter each menu items callback class
                            popmenu_callback_class_ref =  CasDynamicallyCreateMenuCallBackFunctionForSelectchildNode(str(id), mat.name + ',' + node.name, self.setupnode_namestr) 
                            bpy.utils.register_class(popmenu_callback_class_ref)
                            id +=1 
        # Add one mode menu item
        # SELECT NONE callback setup
        popmenu_callback_class_ref = CasDynamicallyCreateMenuCallBackFunctionForSelectchildNode(str(id),'SELECT_NONE,SELECT_NONE', self.setupnode_namestr) 
        bpy.utils.register_class(popmenu_callback_class_ref)

    
    # Buttons execute method. Show a drop down menu of all (filtered) objects in the scene
    def execute(self, context):
        # we dynamically create the callback classes for each menu item here (beacuse we can't register the 
        # callback classes in the draw() method) of CasDynamicallyPopulateMenuForSelectPlane.
        self.createPopMenuCallbackClasses()
        bpy.ops.wm.call_menu(name="cas_menu_populate.select_child_node") 
        return{'FINISHED'}  
   
    # Check to see if we should be displayed
    @classmethod
    def poll(self, context):
        return True
# < !Select child Cutaway Shader button routines >    
'''

# < Set Cutaway plane origin to 3D cursor button >        
# When the user presses the "Set to Cursor" button:
# Sets the origin of the selected cutaway plane to the 3D cursor position.    
class casBtnPlaneOriginToCursor(bpy.types.Operator):
    bl_idname = "cas_btn.origin_to_cursor"
    bl_label = "Set"
    bl_description = "Set the Cutaway Plane origin to the cursor. This can be useful when scaling the plane from a particulr position"
        
    # A link back to the setup node that this button sits in (there may be more that 1 setup node in the tree)
    setupnode_namestr3 = bpy.props.StringProperty(name="")      # passed to us as a keyword argument on creation

    # Buttons execute method. 
    def execute(self, context):
        node_tree = context.space_data.edit_tree
        nodes = node_tree.nodes
        py_node = nodes[self.setupnode_namestr3]          #'Cutaway Shader']
        
        '''
        try:
            cutaway_plane_nameStr =  py_node.get_cutawayPlane_NameStr()
            cutaway_plane_obj = bpy.context.scene.objects[cutaway_plane_nameStr]
        except:
            return{'FINISHED'} 
        '''
        # get the name of the py_node's cutawayPlane.
        # if in no longer exists (e.g. the user deleted it) then bug out.
        cutaway_plane_nameStr =  py_node.get_cutawayPlane_NameStr()
        if (cutaway_plane_nameStr not in bpy.context.scene.objects):
            return{'FINISHED'}
        
       
        
        # If the object is on a layer that is not selected, then bug out (as the following ops will crash)
        # layer select todo: temp enable of the cutawayplanes layer to do the ops - and then restore
        #if py_node.layer_check(cutaway_plane_obj) == False:             #xhere
        #    return{'FINISHED'}
        
        ##saved_layer_settings_list = self.save_layer_settings()
        
        # If there is no active object, make the cutaway plane the active object
        # otherwise we will crash when trying to switch to object mode
        if (bpy.context.scene.objects.active == None):
            cutaway_plane_obj = bpy.context.scene.objects[cutaway_plane_nameStr]
            bpy.context.scene.objects.active = cutaway_plane_obj
        
        # we need to be in object mode to do this work
        bpy.ops.object.mode_set(mode='OBJECT')
                    
        # save the area type -- should be node editor since a node editor button was pressed.
        original_areatype = bpy.context.area.type
        
        # the cursor bpy ops only work from the 3d view context. So, switch to this.
        bpy.context.area.type = "VIEW_3D"
        
        # save the active object (to prevent our tree node disapearing if not pinned)
        active_obj_save = bpy.context.scene.objects.active
        
         # get a reference to the cutaway plnae object
        cutaway_plane_obj = bpy.context.scene.objects[cutaway_plane_nameStr]
        #print("name is ", cutaway_plane_obj.name)
        
        #saved_obj_layer_settings_list = py_node.save_obj_layer_settings(cutaway_plane_obj)
        
        saved_3d_layers_setting_list = py_node.save_3d_view_layer_settings(context.space_data.layers)
        context.space_data.layers = [True] * 20
        
        ### Make all layers enabled - so we can find the cut away plane (if it was on a disabled layer)
        ###bpy.context.scene.layers = [True] * 20 # Show all layers (bug here -- need to restore)
        #bpy.context.object.layers = [True] * 20 # Show all layers (bug here -- need to restore)
        #cutaway_plane_obj.layers = [True] * 20 # Show all layers (bug here -- need to restore)
        
        # store the location of current 3d cursor and the current active object
        # multiply by 1 so we get a copy of the cursor location, not just a reference to the cursor_location
        new_user_global_origin = bpy.context.scene.cursor_location  * 1
        
        # deselect all objects in the scene
        bpy.ops.object.select_all(action='DESELECT')
    
        # Set the cutaway plane as the selected, active object
        cutaway_plane_obj.select = True
        bpy.context.scene.objects.active = cutaway_plane_obj #bpy.context.scene.objects[cutaway_plane_nameStr] #cutaway_plane_obj
   
        # get the global co-ordinates of the center of the cut away plane
        global_center_origin = bpy.context.scene.cursor_location * 1
        
        # move the origin to the new point desired by the user.
        # the user defined cut away plane origin allows the user to scale/rotate the cutwaya plane in the manner they want to
        bpy.context.scene.cursor_location = new_user_global_origin
         
        # set the origin of the selected cutaway plane to the cursor position selected by the user
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        
        # we need to be in edit mode to do this work
        bpy.ops.object.mode_set(mode='EDIT')
        
        # deselect all edges in the  cutaway plane
        bpy.ops.mesh.select_all(action='DESELECT')
        
        # crank up bmesh :-)
        bm = bmesh.from_edit_mesh(cutaway_plane_obj.data) 
        if hasattr(bm.verts, "ensure_lookup_table"): 
            bm.verts.ensure_lookup_table()
        
        # calculate the center origin of the plane in local co-ordinates.
        i = 0.0
        local_center_origin = mathutils.Vector((0.0, 0.0, 0.0))
        for vert in bm.verts:
            local_center_origin += vert.co
            i += 1.0
        local_center_origin = local_center_origin / i 
        
        # we need to be in edit mode to do this work
        bpy.ops.object.mode_set(mode='OBJECT')
        
        #origin_offset = center_origin - edge_center
        
        # calculate the offset between the cutaway plane's origin and its geometrical center
        origin_offset_vector = global_center_origin - new_user_global_origin;
        
        # calculate the offset beween the plane's global venter origin and the user global origin
        origin_offset_point = local_center_origin + origin_offset_vector
        
        
        py_node.restore_3d_view_layer_settings(context.space_data.layers, saved_3d_layers_setting_list)
        #py_node.restore_obj_layer_settings(cutaway_plane_obj, saved_obj_layer_settings_list)
        
        # update the osl cut away shader node with the new offset
        py_node.update_parent_and_child_origins(origin_offset_point)
        
        
        
        # switch back to the users original context
        bpy.context.area.type = original_areatype
        
        # restore the saved active object (to prevent our tree node disapearing if not pinned)
        bpy.context.scene.objects.active = active_obj_save
        
        return{'FINISHED'} 
    
    # Check to see if we should be displayed
    @classmethod
    def poll(self, context):
        return True   
# < !Set Cutaway plane origin to 3D cursor button > 

      
# < Set Cutaway plane origin to geom center >    
class casBtnPlaneOriginReset(bpy.types.Operator):
    bl_idname = "cas_btn.origin_reset"
    bl_label = "Reset"
    bl_description = "Set the origin of the Cutaway Plane to the geometrical center of the plane. This is useful when scaling the plane."
    
    # A link back to the setup node that 'owns' this button (there may be more that 1 setup node in the tree)
    setupnode_namestr4 = bpy.props.StringProperty(name="")      # passed to us as a keyword argument on creation

    # Buttons execute method. 
    def execute(self, context):
        node_tree = context.space_data.edit_tree
        nodes = node_tree.nodes
        py_node = nodes[self.setupnode_namestr4]          #'Cutaway Shader'] 
        
        py_node.origin_reset()
        return{'FINISHED'}   
# < !Set Cutaway plane origin to geom center >

'''
# < Jump To child Cutaway Shader Node Button >
class casBtnJumpTochildNode(bpy.types.Operator):
    bl_idname = "cas_btn.jump_to_child_node"
    bl_label = "Jump To child Node Tree View"
    
    # A link back to the setup node that this button sits in 
    # (note there may be more that 1 setup node in the tree)
    # This parameter is passed to us as a keyword argument on creation
    setupnode_namestr2 = bpy.props.StringProperty(name="")          
      
    # Buttons execute method. 
    def execute(self, context):
        node_tree = context.space_data.edit_tree
        nodes = node_tree.nodes
        py_node = nodes[self.setupnode_namestr2]         #'Cutaway Shader']
        py_node.jump_to_child_node()
        return{'FINISHED'} 
     
    # Check to see if we should be displayed
    @classmethod
    def poll(self, context):
        return True
# < !Jump To child Cutaway Shader Node Button >  
'''

# < Select parent Cutaway Shader Node Button >
class casBtnSelectParentObj(bpy.types.Operator):
    bl_idname = "cas_btn.select_parent_node"
    bl_label = "Select Parent Node"
    bl_description = "Select parent object of this child node."
    
    # A link back to the setup node that this button sits in 
    # (note there may be more that 1 setup node in the tree)
    # This parameter is passed to us as a keyword argument on creation
    setupnode_namestr_spo = bpy.props.StringProperty(name="")          
      
    # Buttons execute method. 
    def execute(self, context):
        node_tree = context.space_data.edit_tree
        nodes = node_tree.nodes
        py_node = nodes[self.setupnode_namestr_spo]         #'Cutaway Shader']
        py_node.select_parent_node()
        return{'FINISHED'} 
     
    # Check to see if we should be displayed
    @classmethod
    def poll(self, context):
        return True
# < !Select parent Cutaway Shader Node Button >  

# < Jump To parent Cutaway Shader Node Button >
class casBtnJumpToparentNode(bpy.types.Operator):
    bl_idname = "cas_btn.jump_to_parent_node"
    bl_label = "Jump To parent Node Tree View"
    bl_description = "A quick way to show the nodetree of this child's parent shader."
    
    # A link back to the setup node that this button sits in 
    # (note there may be more that 1 setup node in the tree)
    # This parameter is passed to us as a keyword argument on creation
    setupnode_namestr90 = bpy.props.StringProperty(name="")          
      
    # Buttons execute method. 
    def execute(self, context):
        node_tree = context.space_data.edit_tree
        nodes = node_tree.nodes
        py_node = nodes[self.setupnode_namestr90]         #'Cutaway Shader']
        py_node.jump_to_parent_node()
        return{'FINISHED'} 
     
    # Check to see if we should be displayed
    @classmethod
    def poll(self, context):
        return True
# < !Jump To parent Cutaway Shader Node Button >  

# < Select all Objects using this Child Shader Button >
class casBtnSelectAllObjectsUsingThisChildNode(bpy.types.Operator):
    bl_idname = "cas_btn.select_all_objects_using_this_child_node"
    bl_label = "Select all Objects using this Child Shader"
    bl_description = "Select all Objects using this Child Shader"
    
    # A link back to the setup node that this button sits in 
    # (note there may be more that 1 setup node in the tree)
    # This parameter is passed to us as a keyword argument on creation
    setupnode_namestr_saoutcs = bpy.props.StringProperty(name="")          
      
    # Buttons execute method. 
    def execute(self, context):
        node_tree = context.space_data.edit_tree
        nodes = node_tree.nodes
        py_node = nodes[self.setupnode_namestr_saoutcs]         #'Cutaway Shader']
        py_node.select_all_objects_using_this_child_node()
        return{'FINISHED'} 
     
    # Check to see if we should be displayed
    @classmethod
    def poll(self, context):
        return True
# < !Select all Objects using this Child Shader Button >  

# < Unlink child Node from parent Node >
class casBtnUnlinkchildNode(bpy.types.Operator):
    bl_idname = "cas_btn.unlink_child"
    bl_label = "Unlink child from parent Node"
    bl_description = "For selected objects using this child shader: Convert this child node into a standalone, non-parented, cutaway shader. A new material copy will be created, so as not to affect objects using the original child node."
    #bl_options = {'REGISTER', 'UNDO'}
    
    # A link back to the setup node that this button sits in (there may be more that 1 setup node in the tree)
    setupnode_namestr2 = bpy.props.StringProperty(name="")      # passed to us as a keyword argument on creation
      
    # Buttons execute method. 
    def execute(self, context):
        node_tree = context.space_data.edit_tree
        nodes = node_tree.nodes
        py_node = nodes[self.setupnode_namestr2]          #'Cutaway Shader']
        py_node.unlink_child()
        return{'FINISHED'} 
     
    # Check to see if we should be displayed
    @classmethod
    def poll(self, context):
        return True
# < !Add Cutaway Plane Button >

# < Warning Dialog: Delete all CutawayShaders -- can't be undone! >
class casWarningDialogOperator(bpy.types.Operator):
    bl_idname = "cas_btn.warning_dialog_operator"
    bl_label = "Warning: Save a bakup copy!"
    bl_description = "Warning: Delete all CutAway Shader nodes? Save a backup copy first!"

    # A link back to the setup node that this button sits in 
    # (note there may be more that 1 setup node in the tree)
    # This parameter is passed to us as a keyword argument on creation
    setupnode_namestr_wdo = bpy.props.StringProperty(name="")     
 
    def execute(self, context):
        self.report({'INFO'}, "Deleting All CutAway Shader Nodes. Bye Bye!")
        node_tree = context.space_data.edit_tree
        nodes = node_tree.nodes
        py_node = nodes[self.setupnode_namestr_wdo]          #'Cutaway Shader']
        py_node.remove_all_cut_away_shader_nodes()
        return {'FINISHED'}
 
    def invoke(self, context, event):
       return context.window_manager.invoke_props_dialog(self, width = 550, height = 200)
   
    def draw(self, context):
        self.layout.label("Delete ALL cutaway shader nodes from ALL materials?")
        #self.layout.label("")
        self.layout.label("(ESC to Cancel)")
        
        #row = self.layout.split(0.25)
        #row.prop(self, "type")
        #row.prop(self, "message")
        #row = self.layout.split(0.80)
        #row.label("") 
        #row.operator("error.ok")
   
    # Check to see if we should be displayed
    @classmethod
    def poll(self, context):
        return True
# < !Warning Dialog: Delete all CutawayShaders -- can't be undone! >




# *************************************************************************************
# *************************************************************************************
#
# CutAwaySetupNode py_node class code
# This is the entry point for the code when the user selects "Shader Effects-> Cutaway Shader"
#
# *************************************************************************************
# *************************************************************************************




# ***************************** Define the Custom Node(s) *****************************
#                   We can create more than one new node if desired
#
# A custom node that allows the OSL cut away shader node to be easily set up
# Specifically, it:
# - Allows the cut away plane object to be selected from a drop down enumeration box,
# - Allows various shader mode selection options to be selected with check boxes
# - Connects all the required user inputs and outputs to the parent shader
# - Creates drivers to link the selected cutaway plane LOC,ROT,SCALE attributes to the OSL cut away shader
# - Creates the OSL shader node an pre-wires the node links for the user (these are really just for show - the drivers do the work)
# - Allows multiple slected objects in the scene to have the same cut away shader added to their existing materials 
#   (there is 1 parent shader and possibly many child shaders that follow the parent's node settings.)
# The general gist from here on is to:
    #   Define class props
    #   Do init:
    #       Define the node's input sockets.
    #       Define the node's output sockets.
    #       Get access to this nodes nodetree and nodetree.nodes functions/properties.
    #       Create the OSL cutaway Shader node.
    #       Link the outputs of this setup helper node to the inputes of the OSL cut away shader node.
    #       Set some user defaults on the OSL shader node.
    #       Group the this helper setup node and the OSL shader node together.
    #       Get access to the group node's nodetree and nodetree.nodes functions/properties.
    #       Create the group node's GROUP Input and Group Output nodes .
    #       Define the input and output socket types for the Group Input and OutPuts.
    #       Associate the input and output sockets to the input and ouput nodes.
    #       Make node links between the Group Input and Output Nodes and the setup helper + OSL shader node.
    #       Note: The links to this custom setup help node are for show only
    #             OSL node divers are set when a new cutaway plane is selected. Other OSL input values are written to directly by the py node code.
    #             The links to the OSL shader node are required and do work as normal.
    
class CutAwaySetupNode(Node):
    #print ("PY NODE INSTANTIATED")
    # Required by the custom node API
    bl_idname = 'CutAwayShaderNodeType'                                 # How this node is referred to in the UI
    bl_label = 'Cutaway Shader'                                         # What's printed on the box
    bl_icon = 'SOUND'                                                   # The icon in the data block view
    bl_options = {'REGISTER', 'UNDO'}
    
  
    # Define props: props get saved with the file
    py_nodename_str  = bpy.props.StringProperty()                       # This python custom node
    osl_nodename_str  = bpy.props.StringProperty()                      # The name of the OSL node that this python custom node controls
    
   
    # Properties used by child nodes (set to '' for parent nodes)
    this_childs_parent_pynode_unique_id_str = bpy.props.StringProperty(default ='')
    orphaned_child_node_bool = bpy.props.BoolProperty()                 # Set to true if a child's parent node no longer exits (e.g. no object uses the material - or the material has been deleted)          
    
    # properties to store user pynode settings
    cutAwayPlaneNameStr = bpy.props.StringProperty()                    # Set when user selects from drop down enumeration box (from the socket input)
    rectangular_circular_int = bpy.props.IntProperty()                  # cutaway draw mode (circular 0, rect 1 , cutaway image 2)
    cutaway_image_path_and_name_str = bpy.props.StringProperty()        # The file path and name of an image that can be used to define the cut away plane shape/transparency
    
    origin_offset = bpy.props.FloatVectorProperty()
    node_is_parent = bpy.props.BoolProperty()                           # false if a child node, true otherwise
    
    
    def cas_frame_change_callback_update_child_nodes_with_keyed_values(scene):
        # Check if global_auto_update_child_nodes_on_frame_change_bool has been defined
        if 'global_auto_update_child_nodes_on_frame_change_bool' not in bpy.context.scene.keys():
            bpy.context.scene['global_auto_update_child_nodes_on_frame_change_bool'] = True
            
        if bpy.context.scene['global_auto_update_child_nodes_on_frame_change_bool'] == False:
            return
            
        #print("frame change: frame" + str(bpy.context.scene.frame_current))
        # iterate over all materials. For parent pynodes - copy any key framed data to the parent osl shader and child osl shaders
        for mat in bpy.data.materials:
            if mat.use_nodes:
                for node in mat.node_tree.nodes:
                    if "Cutaway Shader" in node.name:
                    #if node.name.find("Cutaway Shader") != -1:
                        if node.node_is_parent == True:
                            #if (node.effectmix_float_last_frame_value != node.effectmix_float):
                            #print("PreFrame:Setting effectmix_float for: " + node.name)
                            node.effectmix_float = node.effectmix_float           # setting the property to itself will call the update call back for this property => update this and all child node => update all OSL inputs
 
                            #if (node.rimeffectmix_float_last_frame_value != node.rimeffectmix_float):
                            node.rimeffectmix_float = node.rimeffectmix_float
                      
                            #if (node.edge_fade_distance_float_last_frame_value != node.edge_fade_distance_float_prop): 
                            node.edge_fade_distance_float_prop = node.edge_fade_distance_float_prop  
                                
                            #if (node.edge_fade_sharpness_float_last_frame_value != node.edge_fade_sharpness_float_prop): 
                            node.edge_fade_sharpness_float_prop = node.edge_fade_sharpness_float_prop
                            
                            
                            
    def cas_render_pre_callback_update_child_nodes_with_keyed_values(scene):
        #print("frame change: frame" + str(bpy.context.scene.frame_current))
        # iterate over all materials. For parent pynodes - copy any key framed data to the parent osl shader and child osl shaders
        for mat in bpy.data.materials:
            if mat.use_nodes:
                for node in mat.node_tree.nodes:
                    if "Cutaway Shader" in node.name:
                    #if node.name.find("Cutaway Shader") != -1:
                        if node.node_is_parent == True:
                            #if (node.effectmix_float_last_frame_value != node.effectmix_float):
                            #print("PreFrame:Setting effectmix_float for: " + node.name)
                            node.effectmix_float = node.effectmix_float           # setting the property to itself will call the update call back for this property => update this and all child node => update all OSL inputs

                            #if (node.rimeffectmix_float_last_frame_value != node.rimeffectmix_float):
                            node.rimeffectmix_float = node.rimeffectmix_float
                      
                            #if (node.edge_fade_distance_float_last_frame_value != node.edge_fade_distance_float_prop): 
                            node.edge_fade_distance_float_prop = node.edge_fade_distance_float_prop  
                                
                            #if (node.edge_fade_sharpness_float_last_frame_value != node.edge_fade_sharpness_float_prop): 
                            node.edge_fade_sharpness_float_prop = node.edge_fade_sharpness_float_prop
                        
                        
    # This routine is called before every frame is rendered (see below for more info on this)
    # We check to see if any of our sliders have been animation keyed (i.e check to see if their value has been updated for this new frame).
    # If any of the values have been keyed - then then this py node's osl node needs to be updated - as do all the child nodes.
    '''
    def cas_pre_frame_render_callback(scene):
        # Check if global_auto_update_child_nodes_on_frame_change_bool has been defined
        if 'global_auto_update_child_nodes_on_frame_change_bool' not in bpy.context.scene.keys():
            bpy.context.scene['global_auto_update_child_nodes_on_frame_change_bool'] = True
        
        # check if this needs to execute        
        if (bpy.context.scene['global_auto_update_child_nodes_on_frame_change_bool']):
            #yes we need to execute
            cas_update_child_nodes_with_keyed_values(scene)
    '''
        
    '''
    if (self.effectmix_float_last_frame_value != self.effectmix_float):
        #keyframe_prop_change = True
        self.effectmix_float = self.effectmix_float           # setting the property to itself will call the update call back for this property => update this and all child node => update all OSL inputs
    
    if (self.rimeffectmix_float_last_frame_value != self.rimeffectmix_float):
        self.rimeffectmix_float = self.rimeffectmix_float
        
        #keyframe_prop_change = True
    if (self.edge_fade_distance_float_last_frame_value != self.edge_fade_distance_float_prop):   
        self.edge_fade_distance_float_prop = self.edge_fade_distance_float_prop 
        #keyframe_prop_change = True   
        
    if (self.edge_fade_sharpness_float_last_frame_value != self.edge_fade_sharpness_float_prop):
        self.edge_fade_sharpness_float_prop = self.edge_fade_sharpness_float_prop
        #keyframe_prop_change = True    
        
    # todo:
    # would be faster to use  keyframe_prop_change. Iterate through all the child nodes just once (instead of multiple times as above) 
    # change above ifs to elif           
        self.effectmix_float_last_frame_value = self.effectmix_float;
        print("float value changed", self.effectmix_float)
    #print("Frame Change2", scene.frame_current, self.effectmix_float)  # effectmix_float
    '''
    # There was an issue where key framed values on a parent pynode were not being copied to the child nodes
    # when the time line was moved, or when an animation was being rendered.
    # The callback allows the master pynode to copy the appropriate parameters to all its child nodes (I had tried adding
    # drivers programmatically to do this -- but the child pynodes could not be driven -- maybe this will change as the depsgraph is updated )
    # Note"If there are *alot* of child nodes - then it can take some time to update all the parameters, so it may be worth while)
    # having a check box to turn off the automatic update during render previews.  
    # There was also an issue during the development where the callback seemed to be called twice (this was used at the time to detect
    # materials being changed -- e.g. duplicated -- and dealing with the re-creation of a new parent node, or finding the parent of a 
    # duplicated child node) -- need to re-check this.
        
    # Comment out the unused callback options (some favour rendering, others favour preview)     
    # *** scene_update_post ***    
    # callback_delete_list = []
    # for callback in bpy.app.handlers.scene_update_post:
        # if (callback.__name__ == cas_pre_frame_render_callback.__name__):
            # print ("found " + callback.__name__ + "to delete" )
            # callback_delete_list.append(callback)
        
    # for callback in callback_delete_list:
        # print("Deleting old callback: " + callback.__name__)
        # bpy.app.handlers.scene_update_post.remove(callback)
        
        
    # *** frame_change_pre ***
    # Remove any old callbacks. These accumulate, making debugging hard, and slowing down performance.
    # We can't iterate over a list we're changing, so make a fresh list of functions to delete - and then delete from this list. 
    callback_delete_list = []
    for callback in bpy.app.handlers.frame_change_pre:
        if (callback.__name__ == cas_frame_change_callback_update_child_nodes_with_keyed_values.__name__):
            print ("found frame_change_pre " + callback.__name__ + " to delete" )
            callback_delete_list.append(callback)
                 
    for callback in callback_delete_list:
        print("Deleting old frame_change_pre callback: " + callback.__name__)
        bpy.app.handlers.frame_change_pre.remove(callback)
    
   
    # *** render_pre *** 
    # Remove any old callbacks. These accumulate, making debugging hard, and slowing down performance.
    # We can't iterate over a list we're changing, so make a fresh list of functions to delete - and then delete from this list.     
    callback_delete_list = []
    for callback in bpy.app.handlers.render_pre:                                                                            # <=== render_pre.append
        if (callback.__name__ == cas_render_pre_callback_update_child_nodes_with_keyed_values.__name__):
            #print ("found render_pre " + callback.__name__ + "to delete" )
            callback_delete_list.append(callback)
        
    for callback in callback_delete_list:
        #print("Deleting old render_pre callback: " + callback.__name__)
        bpy.app.handlers.render_pre.remove(callback)

    #print("ADDING PRE FRAME CALLBACK_called once when Blender started or script first run")
    bpy.app.handlers.frame_change_pre.append(cas_frame_change_callback_update_child_nodes_with_keyed_values)                # <=== frame_change_pre  (good for rendering - and updates preview - but can bog down preview)
    bpy.app.handlers.render_pre.append(cas_render_pre_callback_update_child_nodes_with_keyed_values)                        # <=== render_pre.append (good for rendering - but not for preview)
    #bpy.app.handlers.scene_update_post.append(cas_pre_frame_render_callback)     

    
    # --------------------------------------------------------------------------------------------
    # --------------------------------------------------------------------------------------------
    # Init method called by the py_node api when the pynode is first instantiated
    # Method required by the py node API
    #   - Init the py node. 
    #   - Init the osl node
    #   - Create all input and output sockets. 
    #   - init the py-node properties 

    def init(self, context):
        # See if the cutaway shader py and osl files are already in the text block memory.
        cutAwayShader_py_exists = False
        cutAwayShader_osl_exists = False
        for textblock in bpy.data.texts:
            if textblock.name == "CutAwayShader.py":
                cutAwayShader_py_exists = True
            elif textblock.name == "CutAwayShader.osl":
                cutAwayShader_osl_exists = True
            
            # Have we found both files    
            if cutAwayShader_py_exists == True and cutAwayShader_py_exists == True:
                # Yes: no need to keep checking the rest of the text blocks
                break
              
        # load the osl code into the tex block memory if needed   
        #cutAwayShader_osl_exists = False  
        if cutAwayShader_osl_exists == False:
            #cutaway_shader_osl_pathandfile_name = bpy.utils.script_paths()[0] +  '/addons/node_cutaway_shader/CutAwayShader.osl'  #'%saddons%snode_cutaway_shader%sCutAwayShader.py'
            cutaway_shader_osl_pathandfile_name = os.path.join(os.path.dirname(__file__), '..', 'node_cutaway_shader', 'CutAwayShader.osl')
            cutaway_shader_osl_textblock = bpy.data.texts.load(cutaway_shader_osl_pathandfile_name)
             
        #cutAwayShader_py_exists = False
        # load the py code into the text block memory if needed    
        if cutAwayShader_py_exists == False:
            #cutaway_shader_py_pathandfile_name = bpy.utils.script_paths()[0] +  '/addons/node_cutaway_shader/CutAwayShader.py'  #'%saddons%snode_cutaway_shader%sCutAwayShader.py'
            #cutaway_shader_py_pathandfile_name = os.path.join(os.path.dirname(__file__), '..', 'node_cutaway_shader', 'CutAwayShader.py')
            cutaway_shader_py_pathandfile_name = os.path.join(os.path.dirname(__file__), '..', 'node_cutaway_shader', '__init__.py')
            cutaway_shader_py_textblock = bpy.data.texts.load(cutaway_shader_py_pathandfile_name)
            cutaway_shader_py_textblock.name = 'CutAwayShader.py'
            cutaway_shader_py_textblock.use_module = True
            print (cutaway_shader_py_textblock.name)
        
        
        # setup references
        py_node = self                   #  py_node is this cut_away_shader pynode helper. self = nodes['Cutaway Shader']
        nodetree = py_node.id_data
        nodes = nodetree.nodes
        
        py_node.width = 350              # determined by 'hand'1500 * .2
        NODE_X_GAP = 100                # determined by 'hand' - gives a good gap between the nodes.
        NODE_Y_OFFSET = 185             # determined by 'hand' - makes the nodes line up nicely.
        
        # Assign a unique id to this pynode - so that parent nodes may find child nodes and vise versa
        # Note - this routine creates the unique_pynode_id_int property for this node.
        self.get_unique_pynode_id_str__create_if_neccessary(self)
        
        # true if the user needs to enable CPU render mode and/or enable OSL render mode
        self.enable_OSL_bool_prop = (bpy.context.scene.cycles.shading_system == True) and (bpy.context.scene.cycles.device  == 'CPU')  ,
        
        # create the osl cutaway shader node and position next to the cutaway py node.
        osl_node = nodes.new('ShaderNodeScript')
        osl_node.script = bpy.data.texts["CutAwayShader.osl"]
        
        # align the py_node and the osl_node so that all the sockets line up.
        osl_node.location.x = bpy.context.space_data.cursor_location.x + py_node.width + NODE_X_GAP
        osl_node.location.y = bpy.context.space_data.cursor_location.y + NODE_Y_OFFSET
        
        # Save name references to ourselves and the OSL cutaway shader for future use.
        # (There may be more than one setup node and OSL shader node added to the tree by the user)
        self.py_nodename_str  = py_node.name
        self.osl_nodename_str  = osl_node.name
        
        self.node_is_parent = True
        self.orphaned_child_node_bool = False
        
        # set osl cutaway shader node input defaults
        self.rectangular_circular_int = 1                   # 1 (rectangular) is the default
        self.cutaway_image_path_and_name_str = ""           # The user must select the cut away transparency image (if they want one)
        
        osl_node.inputs["DrawMode_circular0_rectangular1"].default_value = self.rectangular_circular_int    # set the OSL shader's draw mode (circular 0, rect 1 , cutaway image 2)
        osl_node.inputs["cutAwayImg"].default_value = self.cutaway_image_path_and_name_str                  # set the OSL shader's away transparency image 
        osl_node.inputs["RimThickness"].default_value = self.rimthickness_float                             # set the OSL Shader's Rim Thickness
        osl_node.inputs["EdgeFadeDistance"].default_value = self.edge_fade_distance_float_prop              # set the OSL Shader's 
        osl_node.inputs["EdgeFadeSharpness"].default_value = self.edge_fade_sharpness_float_prop            # set the OSL Shader's 


        # create setup node output sockets
        outputSkt = py_node.outputs.new('NodeSocketFloat', "Effect Mix" )
        outputSkt = py_node.outputs.new('NodeSocketFloat', "Rim Effect Mix")
        outputSkt = py_node.outputs.new('NodeSocketInt', "Invert Cutaway Bounds")
        outputSkt = py_node.outputs.new('NodeSocketFloat', "Edge Fade Distance")
        outputSkt = py_node.outputs.new('NodeSocketFloat', "Edge Fade Sharpness")
        outputSkt = py_node.outputs.new('NodeSocketInt', "Circular/Planar")
        outputSkt = py_node.outputs.new('NodeSocketVector', "Loc")
        outputSkt = py_node.outputs.new('NodeSocketVector', "Rot")
        outputSkt = py_node.outputs.new('NodeSocketVector', "Size")
        outputSkt = py_node.outputs.new('NodeSocketVector', "OriginOffset")
        outputSkt = py_node.outputs.new('NodeSocketInt', "Inner/OuterMesh")
        outputSkt = py_node.outputs.new('NodeSocketString', "RimSegmentXMLData")
        outputSkt = py_node.outputs.new('NodeSocketFloat', "RimThickness")
        outputSkt = py_node.outputs.new('NodeSocketInt', "RimFillEnable")
        outputSkt = py_node.outputs.new('NodeSocketInt', "RimOcclusionEnable")
        outputSkt = py_node.outputs.new('NodeSocketString', "CutAwayImg")
           
        #  link setup node outputs to osl cutaway shader node inputs in the node editor
        output = py_node.outputs['Effect Mix']
        input = osl_node.inputs['EffectMixFactor']                    # Effect Mix
        nodetree.links.new(output, input)
        
        output = py_node.outputs['Rim Effect Mix']                            
        input = osl_node.inputs['RimEffectMixFactor']                 # Rim Effect Mix
        nodetree.links.new(output, input)
        
        output = py_node.outputs['Invert Cutaway Bounds']                            
        input = osl_node.inputs['InvertCutawayBounds']                # Invert Cutaway Bounds
        nodetree.links.new(output, input)
        
        output = py_node.outputs['Edge Fade Distance']                            
        input = osl_node.inputs['EdgeFadeDistance']                  # Edge Fade Distance
        nodetree.links.new(output, input)
        
        output = py_node.outputs['Edge Fade Sharpness']                            
        input = osl_node.inputs['EdgeFadeSharpness']                  # Edge Fade Sharpness
        nodetree.links.new(output, input)
        
        output = py_node.outputs['Circular/Planar']
        input = osl_node.inputs['DrawMode_circular0_rectangular1']    # Circular/Planar
        nodetree.links.new(output, input)
        
        output = py_node.outputs['Loc']
        input = osl_node.inputs['CutAwayLocation']                    # loc input
        nodetree.links.new(output, input)
        
        output = py_node.outputs['Rot']
        input = osl_node.inputs['Rotation']                           # rot input
        nodetree.links.new(output, input)
        
        output = py_node.outputs['Size']
        input = osl_node.inputs['Scale']                              # size input
        nodetree.links.new(output, input)
        
        output = py_node.outputs['Inner/OuterMesh']
        input = osl_node.inputs['InnerMesh0_OuterMesh1']              # parent/child
        nodetree.links.new(output, input)
        
        output = py_node.outputs['RimSegmentXMLData']
        input = osl_node.inputs['RimSegmentXMLData']                  # rimg segment xml data
        nodetree.links.new(output, input)
        
        output = py_node.outputs['RimThickness']
        input = osl_node.inputs['RimThickness']                       # rim thickness
        nodetree.links.new(output, input)
        
        output = py_node.outputs['RimFillEnable']
        input = osl_node.inputs['RimFillEnable']                      # rim fill enable
        nodetree.links.new(output, input)
        
        output = py_node.outputs['RimOcclusionEnable']
        input = osl_node.inputs['RimOcclusionEnable']                 # rim occlusion enable
        nodetree.links.new(output, input)
        
        output = py_node.outputs['OriginOffset']
        input = osl_node.inputs['OriginOffset']                       # current origin offset
        nodetree.links.new(output, input)
        
        output = py_node.outputs['CutAwayImg']
        input = osl_node.inputs['cutAwayImg']                         # current origin offset
        nodetree.links.new(output, input)
        
               
    '''    
    # This routine is called before every frame is rendered.
    # We check to see if any of our sliders have been animation keyed (i.e check to see if their value has been updated for this new frame).
    # If any of the values have been keyed - then then this py node's osl node needs to be updated - as do all the child nodes.
    def pre_frame_render_callback(self,scene):
        #keyframe_prop_change = False;
        print("internal frame callback called xx" + self.name)
        return
        
        # iterate over all master shaders in te scene
        
        #if (self.effectmix_float_last_frame_value != self.effectmix_float):
            #keyframe_prop_change = True
        self.effectmix_float = self.effectmix_float           # setting the property to itself will call the update call back for this property => update this and all child node => update all OSL inputs
        
        #if (self.rimeffectmix_float_last_frame_value != self.rimeffectmix_float):
        self.rimeffectmix_float = self.rimeffectmix_float
            
            #keyframe_prop_change = True
        #if (self.edge_fade_distance_float_last_frame_value != self.edge_fade_distance_float_prop):   
        self.edge_fade_distance_float_prop = self.edge_fade_distance_float_prop 
            #keyframe_prop_change = True   
            
        #if (self.edge_fade_sharpness_float_last_frame_value != self.edge_fade_sharpness_float_prop):
        self.edge_fade_sharpness_float_prop = self.edge_fade_sharpness_float_prop
            #keyframe_prop_change = True    
            
        # todo:
        # would be faster to use  keyframe_prop_change. Iterate through all the child nodes just once (instead of multiple times as above) 
        # change above ifs to elif           
            #self.effectmix_float_last_frame_value = self.effectmix_float;
            #print("float value changed", self.effectmix_float)
        #print("Frame Change2", scene.frame_current, self.effectmix_float)  # effectmix_float
    
    # Note: We are still in the class definition here.
    # These .append statements onlt get run when the Blender file is opened, or when 
    # the addon is run for the first time in a Blender session.
    # Hence. 'self' has not yet been defined.
    #if (pre_frame_render_callback  in bpy.app.handlers.frame_change_pre):
    #    print("REMOVING")
    #    bpy.app.handlers.frame_change_pre.remove(pre_frame_render_callback)
    
    if (pre_frame_render_callback not in bpy.app.handlers.frame_change_pre):
        print("ADDING frame callback")
        bpy.app.handlers.frame_change_pre.append(pre_frame_render_callback)
    '''    

    # --------------------------------------------------------------------------------------------
    # --------------------------------------------------------------------------------------------
    # GUI Buttons, checkboxes, sliders etc used by the py_node
    #   - Generally these GUI routines are called after button presses, where the button (Operator) code
    #     calls these pynode routines via a reference to this pynode.
    #     The Button operator code itself is always invoked via info defined in the draw_buttons(..) method.
    #
    #   - Some of the routines below are called 'directly' from the draw_buttons(..) method.
    #     This is generally the case if the GUI element that has been edited is a 
    #     Property (e.g. an int, float, bool checkbox, enum cmbobox etc)
    #
    #   - By convention, this code uses the same names for the GUI methods as for the Button (Operator) bl_idname
    #     This allows the flow of the code to be 'easily' followed with Find Next searching.
    #     e.g. Search for "add_inner_solidifier_mesh_and_material"
    #           - The  match in draw_buttons(...), near the bottom of this file
    #             shows what Button Operator is called when the "Solidify Active Object" button is pressed.
    #
    #           - The match in casBtnAddInnerSolidifyMeshAndMaterial(...), near the top of this file
    #             shows the Button Operator code itself. The buttons execute method calls add_inner_solidifier_mesh_and_material(...)
    #             in this pynode.
    #
    #           - The match just below these comments (in this pynode) is the actual add_inner_solidifier_mesh_and_material(...) 
    #             code that carries out the action to add a solidify modifier to the active object, and create an 'inner mesh' material if needed.
    #
    #   - Because several methods are often needed to perform Button Operator or Property modification duties, the methods have been
    #     grouped between < Property Code 'X' Start> and < Property Code 'X' End> comment tags. This (hopefully) makes for easier code reading.
    
    
    # < Invert Cutaway Bounds check box >
    # Invert Cutaway Bounds check box has been pressed
    def invertCutAwayBoundsUpdate(self, context):
        oslNode = self.id_data.nodes[self.osl_nodename_str]      # id_data represents treenode
        if (self.invert_cutaway_bounds_prop):
            oslNode.inputs["InvertCutawayBounds"].default_value = 1
        else:
            oslNode.inputs["InvertCutawayBounds"].default_value = 0  
            
        self.set_invert_cutaway_bounds_prop_for_all_child_nodes()
    
    # Check box to select "fill cutaway with a rim" 
    invert_cutaway_bounds_prop = bpy.props.BoolProperty( 
        name="Invert Cutaway Bounds",
        description="If set: The area outside the cutaway plane will be cutaway.",
        default = False,
        update=invertCutAwayBoundsUpdate)
    # <! Invert Cutaway Bounds check box  !> 
    
    # < Auto Update Child Nodes on preview frame change check box >
    # Auto Update Child Nodes on preview frame change check box has been pressed
    def autoUpdateChildPropsAfterFrameChange(self, context):
        #oslNode = self.id_data.nodes[self.osl_nodename_str]      # id_data represents treenode
        if (self.auto_update_child_props_after_frame_change_bool_prop):
            pass
            #enable the call back
        else:
            pass
            #remove the callback
            
        # Take some action
        # if (self.invert_cutaway_bounds_prop):
            # oslNode.inputs["InvertCutawayBounds"].default_value = 1
        # else:
            # oslNode.inputs["InvertCutawayBounds"].default_value = 0  
            
        # self.set_invert_cutaway_bounds_prop_for_all_child_nodes()
    
    # Check box to select "fill cutaway with a rim" 
    auto_update_child_props_after_frame_change_bool_prop = bpy.props.BoolProperty( 
        name="Auto Update Child Nodes on preview frame change",
        description="If set: In viewport renders, parent shader settings are copied to child nodes on frame changes.",
        default = True,
        update=autoUpdateChildPropsAfterFrameChange)
    # <! Auto Update Child Nodes on preview frame change check box !>
    
    # < Edge Index Slider >                                           
    # The user wants to move the cutaway plane origin to one of the boundary edges.
    # Move the origin to the edge and calculate the offset to where the geometrical center of 
    # the plane is. This offset will be sent to the OSL shader, as the OSL shader always uses the geometrical center
    # of the plane as its reference point for locating all plane edges, as well as defining where any 'cutting away' should begin from.    
    def edgeIndex_update(self, context):
        '''
        try:
            # If there is a plane selected, get access to its data
            cutaway_plane_nameStr =  self.get_cutawayPlane_NameStr()
            cutaway_plane_obj = bpy.context.scene.objects[cutaway_plane_nameStr]
        except:
            # If there is no plane selected then exit.
             return
         '''
        # If there is a plane selected, get access to its data
        cutaway_plane_nameStr =  self.get_cutawayPlane_NameStr()
        if (cutaway_plane_nameStr not in bpy.context.scene.objects):
            return
        
        # Get a reference to the cutaway plane used by this pynode
        cutaway_plane_obj = bpy.context.scene.objects[cutaway_plane_nameStr]

        # If the cutaway plane is on a layer that is not currently selected, then bug out - as the following .ops operations will crash blender
        # layer select dodo: Could do a temp enable of the planes layer to carry out the operation - and then restore the layer to the user default.
        if self.layer_check(cutaway_plane_obj) == False:
            return

        # the cursor bpy ops only work from the 3d view context. So, switch to this.
        original_areatype = bpy.context.area.type
        bpy.context.area.type = "VIEW_3D"
        
        if (bpy.context.scene.objects.active == None):
            bpy.context.scene.objects.active = cutaway_plane_obj
      
        # We must be in object mode to start with
        bpy.ops.object.mode_set(mode='OBJECT')      # <=== edge select - can get bug here
        
        # save the active object (to prevent our tree node disapearing if not pinned)
        active_obj_save = bpy.context.scene.objects.active
        
        #saved_obj_layer_settings_list = self.save_obj_layer_settings(cutaway_obj)
        #save_layers_array = context.space_data.layers
        saved_3d_layers_setting_list = self.save_3d_view_layer_settings(context.space_data.layers)
        
        context.space_data.layers = [True] * 20

        # store the location of current 3d cursor 
        # multiply by 1 so we get a copy of the cursor location, not just a reference to the cursor_location
        saved_cursor_loc = bpy.context.scene.cursor_location  * 1
        
        # deselect all objects in the scene
        bpy.ops.object.select_all(action='DESELECT')
    
        # Set the cutaway plane as the selected, active object
        cutaway_plane_obj.select = True
        bpy.context.scene.objects.active = cutaway_plane_obj 
        
        # we need to be in edit mode to do this work
        bpy.ops.object.mode_set(mode='EDIT')
        
        # de-select all edges in the  cutaway plane
        bpy.ops.mesh.select_all(action='DESELECT')
        
        # crank up bmesh :-)
        bm = bmesh.from_edit_mesh(cutaway_plane_obj.data) 
        if hasattr(bm.verts, "ensure_lookup_table"): 
            bm.verts.ensure_lookup_table()
            
        if hasattr(bm.edges, "ensure_lookup_table"): 
            bm.edges.ensure_lookup_table()
        
        # Get the center of the mesh in local co-ords
        i =0
        center_origin = mathutils.Vector((0.0, 0.0, 0.0))
        for vert in bm.verts:
            center_origin += vert.co
            i += 1
        center_origin = center_origin / i
        
        # force edge selection mode  
        bpy.context.tool_settings.mesh_select_mode = (False, True, False)   
        
         # edge count processing
        bounded_edge_index = self.edgeIndex_int_prop % len(bm.edges)
            
        # select the desired edge
        edge = bm.edges[bounded_edge_index]
        edge_center = self.getEdgeCenter(edge)
        edge.select = True
        
        # move the cursor to the  center of the selected edge
        bpy.ops.view3d.snap_cursor_to_selected() 
        edge.select = False

        # we need to be in object mode for this to work
        bpy.ops.object.mode_set(mode='OBJECT')

        # set the origin of the selected cutaway plane to the cursor position selected by the user
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        
        # calculate the offset between the cutaway plane's origin and its geometrical center
        origin_offset = center_origin - edge_center
        
        # restore the 3D cursor
        bpy.context.scene.cursor_location = saved_cursor_loc

        self.update_parent_and_child_origins(origin_offset)
        
        self.restore_3d_view_layer_settings(context.space_data.layers, saved_3d_layers_setting_list)
        #context.space_data.layers = save_layers_array
        
        # switch back to the users original context
        bpy.context.area.type = original_areatype
        
        # restore the saved active object (to prevent our tree node disappearing if not pinned)
        bpy.context.scene.objects.active = active_obj_save
                            
    edgeIndex_int_prop = bpy.props.IntProperty(
         name="Edge", 
         description = "Set the cut away plane origin to the indexed edge. This is useful if you want to scale the plane while keeping the selected edge at the same position.",
         default=0,
         update=edgeIndex_update)
         
    # helper. Find the center co-ordinate of an edge
    def getEdgeCenter(self, edge):
        v1 = mathutils.Vector(edge.verts[0].co)
        v2 = mathutils.Vector(edge.verts[1].co)
        vec = v2 - v1
        len = vec.length
        vec.normalize() 
        center =  0.5*len*vec + v1
        return center         
    # < !Edge Index Slider > 


    # < Rim Fill check box >
    # Define props with callbacks
    # The Fill Rim toggle button has been pressed
    def fillRimUpdate(self, context):
        oslNode = self.id_data.nodes[self.osl_nodename_str]      # id_data represents treenode
        if (self.fillRim_bool_prop):
            oslNode.inputs["RimFillEnable"].default_value = 1
        else:
            oslNode.inputs["RimFillEnable"].default_value = 0  
    
    # Check box to select "fill cutaway with a rim" 
    fillRim_bool_prop = bpy.props.BoolProperty( 
        name="Fill Rim",
        description="Draw the rim fill between the outer and inner mesh.",
        default = False,
        update=fillRimUpdate)
    # <! Rim Fill check box !>                                                                                        
     
    
    # < Rim Occlusion Enable check box >                                        
    # Check box to select "Rim Occlusion Enable" : Handler  
    def occludeRimUpdate(self, context):
        oslNode = self.id_data.nodes[self.osl_nodename_str]
        if (self.occludeRim_bool_prop):
            oslNode.inputs["RimOcclusionEnable"].default_value = 1
        else:
            oslNode.inputs["RimOcclusionEnable"].default_value = 0
                                               
    # Check box to select "Rim Occlusion Enable" : Property Definition
    occludeRim_bool_prop = bpy.props.BoolProperty( 
        name="Rim Occlusion Enable",
        description="Allow the rim to be occluded by objects inside the cutawy mesh.",
        default = True,
        update=occludeRimUpdate)  
    # < !Rim Occlusion Enable check box >                                            
     
    
    # < Circular / Rectangular drop down box >                                                       
    def upDateDrawModeEnums(self, context):
        # calculate the current selection index from the 'dropdown enumeration box'
        indexInt = 1-eval(self.draw_mode_enum) -1

        theSelection = self.plane_shape_items[indexInt][1]
        oslNode = self.id_data.nodes[self.osl_nodename_str]
        if (theSelection == 'Rectangular'):
              oslNode.inputs["DrawMode_circular0_rectangular1"].default_value = 1
              self.rectangular_circular_int = 1 
              
        elif (theSelection == 'Circular'):
              oslNode.inputs["DrawMode_circular0_rectangular1"].default_value = 0
              self.rectangular_circular_int = 0    
              
        elif (theSelection == 'From Image'):
              oslNode.inputs["DrawMode_circular0_rectangular1"].default_value = 2
              oslNode.inputs["cutAwayImg"].default_value = self.cutaway_image_path_and_name_str
              self.rectangular_circular_int = 2 
        
        self.update_child_node_rect_circular_settings()

              
    # The state of the selection is saved if the blend file is saved (because properties are saved)
    plane_shape_items = (('3', 'From Image', ''), ('2', 'Circular', ''), ('1', 'Rectangular', ''))
    draw_mode_enum = bpy.props.EnumProperty(
        name = "Cutaway Plane Shape", 
        description = "Rectangular, Circular or Image Based cutaway plane", 
        items = plane_shape_items,
        default="1",
        update = upDateDrawModeEnums)
    # <! Circular / Planer drop down box>
    
    # < Edge Fade Distance Slider >
    def edge_fade_distance_update(self, context):
        oslNode = self.id_data.nodes[self.osl_nodename_str]
        oslNode.inputs["EdgeFadeDistance"].default_value = self.edge_fade_distance_float_prop
        self.set_fadedist_and_sharpness_prop_for_all_child_nodes()
        
    edge_fade_distance_float_prop = bpy.props.FloatProperty(
        name = "Distance", 
        description = "The distance that the cutaway edge fades out over.",
        default = 0.0,
        min = 0,
        update = edge_fade_distance_update)
        
    edge_fade_distance_float_last_frame_value = bpy.props.FloatProperty()    # Allows us to detect key frame changes to effectmix_float before each frame is rendered
    edge_fade_distance_float_last_frame_value = edge_fade_distance_float_prop;       
    # <Edge Fade Distance Slider !>
    
    
    # < Edge Fade Sharpness Slider >
    def edge_fade_sharpness_update(self, context):
        oslNode = self.id_data.nodes[self.osl_nodename_str]
        oslNode.inputs["EdgeFadeSharpness"].default_value = self.edge_fade_sharpness_float_prop
        self.set_fadedist_and_sharpness_prop_for_all_child_nodes()
        
    edge_fade_sharpness_float_prop = bpy.props.FloatProperty(
        name = "Sharpness", 
        description = "The sharpness of the cutaway edge. Higher => sharper edge.",
        default = 1,
        min = 1,
        max = 20,
        update = edge_fade_sharpness_update)
        
    edge_fade_sharpness_float_last_frame_value = bpy.props.FloatProperty()    # Allows us to detect key frame changes to effectmix_float when  this variable is checked before each frame is rendered
    edge_fade_sharpness_float_last_frame_value = edge_fade_sharpness_float_prop;
    # <Edge Fade Distance Slider !>
    

    # < Add Helper Material check box >
    # If Checked, the helper material is added to newly created cutaway planes.
    def addMaterialUpdate(self, context):
        oslNode = self.id_data.nodes[self.osl_nodename_str]
    
    # Check box to select "Rim Occlusion Enable" : Property Definition
    addMaterial_bool_prop = bpy.props.BoolProperty( 
        name="Add Red/Green Material",
        description="Adds the Green (cutaway) and Red (don't cutaway) hint colours to the cutaway plane. Automatically sets the cut away planes ray visibility options",
        default = True,
        update=addMaterialUpdate)                                           
    # < !Add Helper Material check box >
    
   
    # < Final Effect Mix Slider >
    # Update the EffectMixFactor input of the OSL cutaway shader
    def effectmix_update(self, context):
        oslNode = self.id_data.nodes[self.osl_nodename_str]
        oslNode.inputs["EffectMixFactor"].default_value = self.effectmix_float
        self.copy_mixfactor_setting_to_child_nodes()
    
    effectmix_float = bpy.props.FloatProperty(
        name = "Final Effect Mix Factor", 
        description = "How much of the cutaway effect to mix into the render. 0 = No cutaway effect.",
        default = 1.0,
        min = 0.0,
        max = 1.0,
        update = effectmix_update)
        
    effectmix_float_last_frame_value = bpy.props.FloatProperty()    # Allows us to detect key frame changes to effectmix_float when  this variable is checked before each frame is rendered
    effectmix_float_last_frame_value = effectmix_float;
    # <!Final Effect Mix Slider !>
    

    # < Rim Thickness Slider >
    def rim_thickness_update(self, context):
        oslNode = self.id_data.nodes[self.osl_nodename_str]
        oslNode.inputs["RimThickness"].default_value = self.rimthickness_float
        
    rimthickness_float = bpy.props.FloatProperty(
        name = "Thickness", 
        description = "The thickness of the rim fill between the inner and outer mesh.",
        default = 0.3,
        min = 0,
        max = 100,
        update = rim_thickness_update)
    # Rim Thickness Slider!>

    
    # < Rim Effect Mix Factor Slider >
    def rim_effect_mix_update(self, context):
        oslNode = self.id_data.nodes[self.osl_nodename_str]
        oslNode.inputs["RimEffectMixFactor"].default_value = self.rimeffectmix_float
             
    rimeffectmix_float = bpy.props.FloatProperty(
        name = "Rim Effect Mix", 
        description = "How much of the rim fill effect to mix into the render. 0 = No rim effect.",
        default = 1.0,
        min = 0,
        max = 1,
        update = rim_effect_mix_update)
        
    rimeffectmix_float_last_frame_value = bpy.props.FloatProperty()    # Allows us to detect key frame changes to effectmix_float when  this variable is checked before each frame is rendered
    rimeffectmix_float_last_frame_value = rimeffectmix_float;
    # <! Rim Effect Mix Factor Slider >
    

    # --------------------------------------------------------------------------------------------
    # --------------------------------------------------------------------------------------------
    #  Helper methods called by the operators (buttons, menus defined above) used by this py_node
    
    
    # Called from button: The User has selected a cut away plane. 
    #   - Also called from parent node when copying parent settings over to a child node
    #   - Setup drivers so the OSL shader uses this plane for its calculations 
    #   - Re-draw the scene
    def setNewCutawayPlane(self,newCutawayPlaneStr):
        # check if the plane exists (the user may be trying to set the child node without having chosen a plane yet)
        if (newCutawayPlaneStr in bpy.context.scene.objects):
            # Check if the cutaway plane has changed (some times just the number of edges etc change - not the actual plane)
            cutawayPlaneChanged = True
            if (self.cutAwayPlaneNameStr == newCutawayPlaneStr):
                cutawayPlaneChanged = False
                
            self.cutAwayPlaneNameStr = newCutawayPlaneStr
            
            # save the users original context
            if (bpy.context.area == None):
                return
            
            original_areatype = bpy.context.area.type
            
            # bpy.ops.object.select_all only work from the 3d view context. So, switch to this.
            bpy.context.area.type = "VIEW_3D"
            
            if (bpy.context.scene.objects.active == None):
                bpy.context.scene.objects.active = bpy.context.scene.objects[newCutawayPlaneStr]
            
            # we need to be in object mode to do this work
            bpy.ops.object.mode_set(mode='OBJECT')
            
            # xx save the active object (to prevent our tree node disappearing if not pinned)
            active_obj_save = bpy.context.scene.objects.active
            
            # Select the cut away plane. bpy.ops.object.mode_set(mode='OBJECT') will crash if the last active plane was just deleted - this fixes the crash
            bpy.context.scene.objects.active = bpy.context.scene.objects[newCutawayPlaneStr]
            
            # bpy.ops.object.select_all only work from the 3d view context. So, switch to this.
            #bpy.context.area.type = "VIEW_3D"
            
             # Save the layers that the user has enabled
            #saved_layer_settings_list = self.save_layer_settings()
            
            # Make all layers enabled - so we can find the cut away plane (if it was on a disabled layer)
            #bpy.context.scene.layers = [True] * 20 # Show all layers (bug here -- need to restore)
            #bpy.context.scene.objects.active = bpy.context.scene.objects[newCutawayPlaneStr]
            
            # we need to be in object mode to do this work
            #bpy.ops.object.mode_set(mode='OBJECT')
            
            # save the active object (to prevent our tree node disappearing if not pinned)
            #active_obj_save = bpy.context.scene.objects.active
            
            #get a reference to the OSL cutaway shader
            py_node = self
            nodetree = py_node.id_data
            nodes = nodetree.nodes
            osl_node = nodes[self.osl_nodename_str]  #'Script'
            
            # add the drivers that drive the new cutaway plane loc, rot and scale into the OSL shader
            # no need to re-add drivers if there has been no plane change
            if (cutawayPlaneChanged):
                self.addDriversToCutawayShaderOslScriptNode(newCutawayPlaneStr, osl_node) 

            ob = bpy.context.scene.objects[newCutawayPlaneStr]
            if (ob != None):
                #bpy.ops.object.select_all(action='DESELECT')
                bpy.ops.object.mode_set(mode='OBJECT')
                RimSegmentXMLDataStr = self.update_rim_segment_data(ob)
                if (self.node_is_parent == True):
                    self.copy_new_cutaway_plane_settings_to_child(newCutawayPlaneStr, RimSegmentXMLDataStr)

                # Ensure that at least one of the layers that the object appears on is enabled
                for i in range (len(bpy.context.scene.layers)):
                    if ob.layers[i] == True:
                        bpy.context.scene.layers[i] = True
                        bpy.context.space_data.layers[i] = True
                        break
                # a hack to get the 3D rendered scene to update after choosing a new cutaway plane
                ob.select = True
                ob.delta_location=(0.0, 0.0, 0.0)
            
            # This prevents the tree node jumping to the new plane material.
            if (active_obj_save != None):
                bpy.context.scene.objects.active = active_obj_save
             
            # save the users original context
            bpy.context.area.type = original_areatype
        else:
            # The cutaway plane no longer exists
            self.cutAwayPlaneNameStr = ""
      
    # The cutawayplane has been changed (or reselected/refreshed)
    # copy the relevant guff, given to us by our parent, into our child settings 
    # If this is called - we are a child node  
    def set_child_cutaway_plane(self, newCutawayPlaneStr, RimSegmentXMLDataStr):
        # Check if the cutaway plane has changed (some times just the number of edges etc change - not the actual plane)
        cutawayPlaneChanged = True
        if (self.cutAwayPlaneNameStr == newCutawayPlaneStr):
            cutawayPlaneChanged = False
            
        self.cutAwayPlaneNameStr = newCutawayPlaneStr
        
        #get a reference to the OSL cutaway shader
        nodetree = self.id_data
        nodes = nodetree.nodes
        osl_node = nodes[self.osl_nodename_str]  #'Script'
        
        # add the drivers that drive the new cutaway plane loc, rot and scale into the OSL shader
        # no need to re-add drivers if there has been no plane change
        if (cutawayPlaneChanged):
            self.addDriversToCutawayShaderOslScriptNode(newCutawayPlaneStr, osl_node)
          
        # copy over the rim segment data XML string (this defines where the edeges are on our cutaway plane    
        osl_node = self.id_data.nodes[self.osl_nodename_str]
        osl_node.inputs["RimSegmentXMLData"].default_value = RimSegmentXMLDataStr 
        
     
    # The user has pressed the refresh cutaway plane button.
    # THis is a handy shortcut, and has the same effect as re-choosing the cutaway plane
    # This is used when the outline of the cutaway plane has changed (vertices added/removed/moved).
    def refresh_cutaway_plane(self):
        # If the cutaway plane vertices have been edited - we need to re-calculate where the geometrical
        # center is for the plane. All OSL shading is performed wrt to this calculated origin - or offsets from it.
        # temp: update our name in case the user changed it.
        #self.mat_name_str = self.get_mat_idstr()
        
        #refresh the actual plane
        self.origin_reset()  
        self.setNewCutawayPlane(self.cutAwayPlaneNameStr)
        
    # --------------------------------------------------------------------------------------------
    # Driver Helper methods called when adding a new cutaway plane
    # Create the driver that links the LOC, ROT or SCALE of the cutaway plane to the OSL Shader
    def addDriver(self, src_obj_name_str, transform_type_str, driven_node, driven_node_input_str):
        driven_node_input = driven_node.inputs[driven_node_input_str]
        
        for x in range(0, 3):
            drv = driven_node_input.driver_add('default_value',x)
            drv.driver.type = 'SCRIPTED'
            drv.driver.show_debug_info = True
            drv.driver.expression = "var"
            srcVar = drv.driver.variables.new()
            srcVar.name = "var"
            
            if (x == 0): xyz_str = '_X'
            elif (x == 1): xyz_str = '_Y'
            elif (x == 2): xyz_str = '_Z'
            
            srcVar.type = 'TRANSFORMS'
            srcVar.targets[0].id = bpy.context.scene.objects[src_obj_name_str]
            srcVar.targets[0].transform_type = transform_type_str + xyz_str
            srcVar.targets[0].transform_space = 'WORLD_SPACE'
     
    # Link the Loc, Rot and Scale of the cutaway plane to the OSL shader using Drivers   
    def addDriversToCutawayShaderOslScriptNode(self,cutAwayPlaneStr,  cutaway_shader_node):
        self.addDriver(cutAwayPlaneStr, 'LOC', cutaway_shader_node, 'CutAwayLocation')
        self.addDriver(cutAwayPlaneStr, 'ROT', cutaway_shader_node, 'Rotation')
        self.addDriver(cutAwayPlaneStr, 'SCALE', cutaway_shader_node, 'Scale')  
        
        
    # Add a driver to copy the parent mixFactor to parent OSL and child OSL nodes.
    # This was required because key frame updates were not being copied from the parent to child shaders,
    # even though the copy routine was called every 'pre' frame.    
    def addMixFactorDriver(self, driven_osl_node_name_str): 
        #print("driver entered")
        # driven value
        driven_node_input = self.id_data.nodes[driven_osl_node_name_str].inputs['EffectMixFactor']  # id_data represents treenode
        drv = driven_node_input.driver_add('default_value')
        drv.driver.type = 'SCRIPTED'
        drv.driver.show_debug_info = True
        drv.driver.expression = "var"
        
        
        
        #source data for driver
        srcVar = drv.driver.variables.new()
        srcVar.name = "var"
        srcVar.type = 'SINGLE_PROP'
        
        srcVar.targets[0].id_type = 'NODETREE'                                                      #<== These lines took several hours to figure out!!!
        srcVar.targets[0].id = self.id_data     # the node tree for this py node                    #<==
        srcVar.targets[0].data_path =  "nodes[\"" + self.py_nodename_str + "\"].effectmix_float"    #<==
        
        #srcVar.targets[0].id_type = 'MATERIAL'                                                     
        #srcVar.targets[0].id = bpy.context.active_object.material_slots["Material"].material.id_data                   
        #srcVar.targets[0].data_path =  "material.node_tree.nodes[\"" + self.py_nodename_str + "\"].effectmix_float"            
        #C.active_object.active_material.node_tree.nodes["Cutaway Shader"].effectmix_float
        #material_slots["Material"].material.node_tree.nodes["Cutaway Shader"].effectmix_float
          
    # --------------------------------------------------------------------------------------------  
 
    # Returns true if the passed object is on one of the displayed layers.   
    # Note: The layer check routine only processes scene.layers
    # If the user has "un-sync'd" their 3D view - then the object's layer may be hidden in this particular 3D view.
    def layer_check(self, obj):
        is_visible = False
        for i  in range(0, len(bpy.context.scene.layers)): 
            if obj.layers[i]  and bpy.context.scene.layers[i]:
                is_visible = True
                break
        return is_visible
    

    # Returns true if the passed object is on one of the displayed layers in the current screen context 
    # (e.g. this screen may not be sync'd with other screen spaces that have the layer in question enabled)
    def context_layer_check(self, context, obj):
        is_visible = False
        for i  in range(0, len(context.scene.layers)):                                  # naughty hard code of 20 layers
            if obj.layers[i]  and context.scene.layers[i]:
                is_visible = True
                break
        return is_visible

#    # called by the parent so we can jump to the parent node tree using a button (i.e we must be a child)    
#    def set_parent_mat_and_node_link_strs(self, mat_idstr , node_name_str, parent_pynode_unique_id_str): #pchng2ok   xxx erase
#        self.parent_cshader_mat_idstr = mat_idstr 
#        self.parent_node_name_str = node_name_str 
#        self.node_is_parent = False                                         # dsw check
#        
#        #doubler
#        self.this_childs_parent_pynode_unique_id_str = parent_pynode_unique_id_str
    
    # called by the parent so we can jump to the parent node tree using a button (i.e we must be a child)      
    #doubler  
    def make_a_child_node(self, parent_pynode_unique_id_str):
        self.node_is_parent = False
        self.orphaned_child_node_bool = False
        self.this_childs_parent_pynode_unique_id_str = parent_pynode_unique_id_str
        
        # Set the OSL node to the inner mesh setting
        oslNode = self.id_data.nodes[self.osl_nodename_str]
        oslNode.inputs["InnerMesh0_OuterMesh1"].default_value = 0
        

    def copy_mixfactor_setting_to_child_nodes(self):
        self.carry_out_action_on_this_parents_child_nodes_b('COPY_MIX_FACTOR_TO_CHILD')
     
    # called by the parent when the effect mix changes (i.e we must be a child)    
    def set_cutaway_mix_float(self, effectmix):
        #print(self.py_nodename_str + ": copying effect mix to child node")
        self.effectmix_float = effectmix
        oslNode = self.id_data.nodes[self.osl_nodename_str]
        oslNode.inputs["EffectMixFactor"].default_value = self.effectmix_float
    
    def xxxNodex(self):
        callback_delete_list = []
        for callback in bpy.app.handlers.frame_change_pre:
            if (callback.__name__ == cas_pre_frame_render_callback.__name__):
                print ("found frame_change_pre " + callback.__name__ + " to delete" )
                callback_delete_list.append(callback)
                 
        for callback in callback_delete_list:
            #print("Deleting old frame_change_pre callback: " + callback.__name__)
            bpy.app.handlers.frame_change_pre.remove(callback)
        

    # Copy the important settings from this parent node to all its child nodes.
    def copy_parent_settings_to_all_child_nodes(self):
        # don't do if we are a child node
        if (self.node_is_parent == False):
            return
        
        self.carry_out_action_on_this_parents_child_nodes_b('COPY_PARENT_SETTINGS_TO_CHILD')
        
        
    # Copy the the new cutaway plane selection settings to the child nodes
    def copy_new_cutaway_plane_settings_to_child(self, new_cutaway_plane_name_str, rim_segment_data_str):
        # don't do if we are a child node 
        if (self.node_is_parent == False):
            return
        
        self.carry_out_action_on_this_parents_child_nodes_b('COPY_NEW_CUTAWAY_PLANE_SETTINGS_TO_CHILD', new_cutaway_plane_name_str, rim_segment_data_str)
     
    # If this is called, we are a parent node
    # self.invert_cutaway_bounds_prop to all child nodes    
    def set_invert_cutaway_bounds_prop_for_all_child_nodes(self):
        # don't do if we are a child node
        if (self.node_is_parent == False):
            return
        self.carry_out_action_on_this_parents_child_nodes_b('COPY_INVERT_CUTAWAY_BOUNDS_TO_CHILD')   
      
    # If this is called, we are a child node    
    # set self.invert_cutaway_bounds_prop to match the parent node (as the user has probably just changed it in the parent node)
    def copy_invert_cutaway_bounds_to_child(self, invert_prop_bool):  # #self.invert_cutaway_bounds_prop
        # Setting this property will force the property update routine to update the OSL node
        self.invert_cutaway_bounds_prop = invert_prop_bool
        
    # If this is called, we are a parent node    
    def set_fadedist_and_sharpness_prop_for_all_child_nodes(self):
        # don't do if we are a child node
        if (self.node_is_parent == False):
            return
        self.carry_out_action_on_this_parents_child_nodes_b('COPY_FADEDIST_AND_SHARPNESS_TO_CHILD') 
     
     # If this is called, we are a child node    
    def copy_fadedist_and_sharpness_to_child(self, fade_dist_float, fade_sharpness_float):
        self.edge_fade_distance_float_prop = fade_dist_float
        self.edge_fade_sharpness_float_prop = fade_sharpness_float
        
    # Copy the important settings from this parent to the given child node. 
    # If this is called we are a parent. The child pynode is passed as a parameter
    def copy_parent_settings_to_child(self, child_py_node):
        #print("******************************************call test1")
        # don't do if we are a child node (this should not really happen)
        if (self.node_is_parent == False):
            return
        
        #the_mat_idstr = self.get_mat_idstr()                                                        #doubleox
        
        parent_pynode_unique_id_str = self.get_unique_pynode_id_str__create_if_neccessary(self)     #doubler
        
        # get the child pynode's OSL node and set the origin offset to the parents origin offset
        osl_node = child_py_node.id_data.nodes[child_py_node.osl_nodename_str]
        osl_node.inputs["OriginOffset"].default_value = self.origin_offset
        
        
        child_py_node.setNewCutawayPlane(self.cutAwayPlaneNameStr) 
        #print ("setting new plane ", self.cutAwayPlaneNameStr)
        child_py_node.set_child_rect_circular_settings(self.rectangular_circular_int, self.cutaway_image_path_and_name_str)
        #child_py_node.set_parent_mat_and_node_link_strs(the_mat_idstr, self.name, parent_pynode_unique_id_str) #doubler #doubleox added parent_pynode_unique_id_str parm. next step get rif of the_mat_idstr
        child_py_node.make_a_child_node(parent_pynode_unique_id_str)
        
        child_py_node.set_cutaway_mix_float(self.effectmix_float)
        child_py_node.copy_fadedist_and_sharpness_to_child(self.edge_fade_distance_float_prop, self.edge_fade_sharpness_float_prop)
        child_py_node.copy_invert_cutaway_bounds_to_child(self.invert_cutaway_bounds_prop)
        
        
        
    
    '''   
    def jump_to_child_node(self):  
        active_mat_index, child_node = self.get_child_node()
        if (child_node != None):
            bpy.context.space_data.pin = False
            bpy.context.object.active_material_index = active_mat_index
            bpy.ops.node.select_all(action='DESELECT')
            child_node.select = True
            #bpy.ops.node.view_selected()
    ''' 
    # Called after Manual refresh button pressed or auto refresh update button pressed
    def manual_refresh_child_nodes_after_frame_change(self):  
        # iterate over all materials. For parent pynodes - copy any key framed data to the parent osl shader and child osl shaders
        # this is the same routine as xxx - except the update of values to child nodes is forced.
        for mat in bpy.data.materials:
            if mat.use_nodes:
                for node in mat.node_tree.nodes:
                    if "Cutaway Shader" in node.name:
                        if node.node_is_parent == True:
                            #if (node.effectmix_float_last_frame_value != node.effectmix_float):
                            #print("Refresh:Setting effectmix_float for: " + node.name)
                            node.effectmix_float = node.effectmix_float           # setting the property to itself will call the update call back for this property => update this and all child node => update all OSL inputs
                            node.rimeffectmix_float = node.rimeffectmix_float
                            node.edge_fade_distance_float_prop = node.edge_fade_distance_float_prop  
                            node.edge_fade_sharpness_float_prop = node.edge_fade_sharpness_float_prop
                            
    
    # Called when the user pressed the Center (cutawayPlane origin) button 
    def origin_reset(self):
        cutaway_plane_nameStr =  self.get_cutawayPlane_NameStr()
        
        if (cutaway_plane_nameStr not in bpy.context.scene.objects):
              return
        
        cutaway_plane_obj = bpy.context.scene.objects[cutaway_plane_nameStr]
        
        # If there is no active object, make the cutaway plane the active object
        # otherwise we will crash when trying to switch to object mode
        if (bpy.context.scene.objects.active == None):
            bpy.context.scene.objects.active = cutaway_plane_obj
        
        #print (cutaway_plane_obj, cutaway_plane_obj.name)
          
        # we need to be in object mode to do this work
        bpy.ops.object.mode_set(mode='OBJECT')
            
        # the cursor bpy ops only work from the 3d view context. So, switch to this.
        original_areatype = bpy.context.area.type
        bpy.context.area.type = "VIEW_3D"
        
        saved_3d_layers_setting_list = self.save_3d_view_layer_settings(bpy.context.space_data.layers)
        bpy.context.space_data.layers = [True] * 20
        
        # save the active object (to prevent our tree node disappearing if not pinned)
        active_obj_save = bpy.context.scene.objects.active
        
        # deselect all objects in the scene
        bpy.ops.object.select_all(action='DESELECT')
    
        # Set the cutaway plane as the selected, active object
        cutaway_plane_obj.select = True
        bpy.context.scene.objects.active = cutaway_plane_obj 

        # set the origin of the object to its geometrical center
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')          
  
        # update the osl cut away shader node with the new offset, in this case (0, 0, 0) 
        self.update_parent_and_child_origins(bpy.context.scene.cursor_location  * 0)
        
        self.restore_3d_view_layer_settings(bpy.context.space_data.layers, saved_3d_layers_setting_list)
  
        # switch back to the users original context
        bpy.context.area.type = original_areatype
        
        
        
        # restore the saved active object (to prevent our tree node disappearing if not pinned)
        bpy.context.scene.objects.active = active_obj_save

    
    # Return a reference to our parent node based on the parents cshader_mat_idstr       
    # If this is called, we are a child node
    #doubler get_parent_node
    def get_parent_pynode(self):
        if (self.this_childs_parent_pynode_unique_id_str == ''):                    # dw to do add this into the normal properties
            # We can't be a child node because we don't have a copy of our parent's pynode unique id
            return None
        
        # iterate over all materials and all treenodes and all nodes until we find our parent Cutaway Shader pynode.
        for mat in bpy.data.materials:
            if mat.use_nodes:
                for node in mat.node_tree.nodes:
                    #if node.name.find("Cutaway Shader") != -1:
                    if "Cutaway Shader" in node.name:
                        if self.this_childs_parent_pynode_unique_id_str == self.get_unique_pynode_id_str__create_if_neccessary(node):
                            # we have found our parent. Return its pynode reference
                            return node
        # Our parent pynode was not found - so return None
        return None
        
        
    
    # Called from button: The user wants to create a new cutaway plane
    # - Add a new, uniquely numbers, cut away plane to the scene.
    # - Add a helper Red/Green material to the plane. (Green is the cutaway side. Red is the 'do not cutaway' side).
    # - Make the plane invisible to the final render (no cast shadows, not visible to the camera etc).
    # This method is called from casBtnAddCutawayPlane(...) when the button is pressed.
    def addNewCutawayPlane(self, context, material):
        
        # save the users original context
        original_areatype = bpy.context.area.type
        
        # This will be used to prevent the node tree jump to the new plane
        active_obj_save = context.scene.objects.active
        
        # some bpy ops only work from the 3d view context. So, switch to this.
        original_areatype = bpy.context.area.type
        bpy.context.area.type = "VIEW_3D"
        if (bpy.context.mode != "OBJECT"):
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.area.type = original_areatype 
        
        # Get the current active object (if any). 

        # Add a new cutaway plane to the scene
        bpy.ops.mesh.primitive_plane_add('INVOKE_REGION_WIN')
        plane = context.scene.objects.active
        
        # set default plane dimensions to 2 by 2 Blender units (the default new plane size)   
        plane.dimensions = 2, 2, 0.0

        #scale
        bpy.ops.object.transform_apply(scale=True)
        
        # Count how many auto created cutaway planes there already are
        ob_names_str = ""
        filter_str = 'cutAwayPlane'
        id = 0
        for i, obj in enumerate(bpy.context.scene.objects): # iterate over all objects in the scene
            if (obj.type == 'MESH'):                        # only process mesh objects
                if  filter_str in obj.name:                 # only process mesh objects with the filter_str in their name 
                    id +=1  
        
        # make the name of the new cutaway plane one higher than the last.
        id += 1           
        nameStr =  "cutAwayPlane."  + str(id)
        plane.name = nameStr  
        
        # Ensure the cutaway plane cannot be seen in the final render (or affect shadows etc)
        plane.cycles_visibility.camera = False
        plane.cycles_visibility.diffuse = False
        plane.cycles_visibility.glossy = False
        plane.cycles_visibility.transmission = False
        plane.cycles_visibility.shadow = False
        plane.cycles_visibility.scatter = False
        bpy.context.object.hide_render = True  
        
        # Apply the green (ok to cutaway face) and red (not ok to cut away face) helper texture if the user wants it
        if self.addMaterial_bool_prop:
            plane.data.materials.append(material)
            
        # let the shader know it's got a new cutaway plane to work with.
        # to do : auto linking of inner mesh material.
        self.setNewCutawayPlane(nameStr)
        
        bpy.context.area.type = "VIEW_3D"
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # switch back to the users original context
        bpy.context.area.type = original_areatype

        # This prevents the tree node jumping to the new plane material.
        bpy.context.scene.objects.active = active_obj_save
        

    def open_image_dialog(self, filenameAndPath):
        #blender_file_path =  bpy.path.abspath("//")        
        #the_filepath = bpy.path.relpath(filenameAndPath, start = blender_file_path)
        #the_filepath = bpy.path.relpath(filenameAndPath)   
        the_filepath = bpy.path.relpath(filenameAndPath) 
        ##print("aaaa", filenameAndPath)
        ##print("bbbb", the_filepath)
        
        
        #self.cutaway_image_path_and_name_str = os.path.relpath(filenameAndPath)
        self.cutaway_image_path_and_name_str = the_filepath #os.path.relpath(the_filepath)
        oslNode = self.id_data.nodes[self.osl_nodename_str]
        oslNode.inputs["cutAwayImg"].default_value = self.cutaway_image_path_and_name_str
        self.update_child_node_rect_circular_settings()
        #print (self.cutaway_image_path_and_name_str)

     
    # Called after the "Add" ChildNodes to selected button pressed in the draw method    
    # Iterate through all the selected ojects in the scene. Insert a child cutaway node
    # (referenced to this parent) to all the materials used by this object. 
    # If the object has no material, then create a defualt one.
    def add_child_nodes_to_selected(self):
        # handy constants
        cutaway_nodes_width = 1000
        NODE_Y_OFFSET = 185
        
        # make this a user setting
        add_defualt_mat_bool = True
        make_duplicate_copy = True
        
        bpy.ops.object.mode_set(mode='OBJECT')
        
        duplicated_material_name_dict = {}
        
        save_active_obj = bpy.context.scene.objects.active
        
        parent_py_node_unique_id_str = self.get_unique_pynode_id_str__create_if_neccessary(self)             # doubler
        
        # Make a list of the selcted objects for us to iterate over - we don't want to modify a list we are iterating over
        # We are going to select one object at a time after this. 
        selected_obj_list = []
        for obj in bpy.context.selected_objects:
            selected_obj_list.append(obj)
            
        for obj in selected_obj_list:
            obj.select = True
            bpy.context.scene.objects.active = obj
            
            # we can only add child nodes to objects that support materials (e.g. not cameras etc)
            do_not_add = True
            if (obj.type == 'MESH' or obj.type == 'CURVE' or obj.type == 'SURFACE' or obj.type == 'META' or obj.type == 'FONT'):
                do_not_add = False
             
            # if this obj is not supported - continue to the next obj 
            if (do_not_add):
                continue  
            
            #print(obj.name)
            
            # Check all the material slots of the object
            # If we find a usable one - we will add the cut away shader to it
            # If we don't find a usable ine, we will create/add a default cutaway shader material.
            index = 0
            #found_material_output = False
            new_diffuse_color = (1, 0, 1, 1)            # (R, G, B, A) = (1, 0, 1, 1) , a default crimson color to denote this is a completely new material added by the cutaway shader.
            for matslot_index, matslot in enumerate(obj.material_slots):
                found_material_output = False
                print (matslot.material, index)
                # Is the slot empty?
                if (matslot.material == None):
                    # There is a matslot - but no material assigned. clean these out - they just get in the way!
                    obj.active_material_index = index
                    bpy.ops.object.material_slot_remove()
                    
                # does that material use nodes and have the required material output node?
                elif (matslot.material.use_nodes == False):
                    # if we are here, the material is defined - but does not use nodes (i.e. is just a diffuse color for cycles)
                    # delete the material -- we'll create a new node based one in its place.
                    # save the diffuse color
                    new_diffuse_color = matslot.material.diffuse_color
                    
                    # erase the slot
                    obj.active_material_index = index
                    bpy.ops.object.material_slot_remove()
                else:  
                     # if we are here, the material is defined and uses nodes.                                                     #if(matslot.material.use_nodes):
                    nodes = matslot.material.node_tree.nodes
                    # does the node tree contain a material output?
                    if ("Material Output" in nodes.keys()):
                        # We've found a usable material (we won't need to create/add one).
                        # Set the flag that will prevent a new material from being added
                        found_material_output = True
                        # (section move note below XXXX)
                
                # let's look at the next slot in the material        
                index += 1
            
            
                create_new_mat = False        
                numslots = len(obj.material_slots.items()) 
                
                # Did we find a usable material to add the cutaway shader to?    
                if (numslots == 0 or  found_material_output == False or matslot.material == None):
                    # No we didn't, so we will have to create one
                    create_new_mat = True
                 
                # If we didn't find a usable material, we will need to create a default one / add the existing default one           
                if (create_new_mat and add_defualt_mat_bool):
                    # This obj has no materials.  Add a default material to this new child object.
                    child_py_node = self.add_default_child_material_to_obj((new_diffuse_color[0], new_diffuse_color[1],new_diffuse_color[2],1), inner_mesh_bool = False)   # (1, 0, 1, 1) (r,g,b,a) 
                    
                    self.append_child_unique_pynode_id_to_parents_master_child_dict(child_py_node)            #doubler  see ****** above for #doubleo
                    thestr = child_py_node.make_a_child_node(parent_py_node_unique_id_str)                    #DOUBLErx
                    self.copy_parent_settings_to_child(child_py_node)
                    
                    # continue to the next obj that needs a child node added
                    continue
                
                 
                # *** If we are here we can try and add a cutaway shader into this material slot  ***
                # <=== Should this section be put above (see XXXX)
                node_tree = matslot.material.node_tree
                outmat_node  = nodes["Material Output"]      # there can be only one ... [outMat node]
                surface_skt =  outmat_node.inputs["Surface"]
                
                # we don't (yet) deal with volume shaders 
                volume_skt =  outmat_node.inputs["Volume"]
                if (volume_skt.is_linked):
                    # - so look at next material if this is a volumetric materials for child nodes (parent nodes are ok - as these are added manually)
                    continue
                # <==== Section move end?
                
                # get the socket that connects to the material output node
                if (len(surface_skt.links) == 0):
                    continue
                
                surface_skt_feeder_skt = surface_skt.links[0].from_socket
                
                # we don't  add child cutaway shader nodes to cut away planes   
                if (surface_skt_feeder_skt.node.name.find("cutAwayMix") > -1):    
                    continue
                
                # We don't add another a child if there is already an OSL node present.
                if hasattr(surface_skt_feeder_skt.node, "script"): 
                    #if (surface_skt_feeder_skt.node.script.name.find("CutAwayShader") > -1):  
                    if "CutAwayShader" in surface_skt_feeder_skt.node.script.name:
                        continue
                    
                #print("got through")
                    
                # Iterate over the node tree. If we are already a parent in this node tree- don't automatically add a child to the node tree too.
                dont_add_child = False
                for a_node in nodes:
                    #print(a_node)
                    if  (a_node == self): 
                        # If we are here, then this node tree already contains 'us' as a parent.
                        # We don't want to automatically add a child node to ourselves.
                        dont_add_child = True
                        continue
                    
                    # We don't want to add a child shader to the material if there is already a child shader with the same parent
                    #if  'Cutaway Shader' in a_node.name and a_node.parent_node_name_str == self.py_nodename_str:
                    #    print('BLOCKED')
                    #    dont_add_child = True
                    #    continue
                        
                if (dont_add_child):
                    # We don't want to automatically add a child node to ourselves or to materials that already have a child shader with this parent
                    # continue the for loop that iterates through object matslots, and objects in the scene.
                    continue
                
                # ***** If we are here this object is about to have a child cut away node added ****
                # If the user has selected 'make_duplicate_copy' - then we want to make a copy of this objects material slots and materials before adding the cut away shader in
                # A duplicate can be useful when a material is shared by many objects (the extreme case is when there is just one material!)
                # but the user only wants to have a cutaway shader only affect selected objects.
                # Note: When child notes are added in a particular operation (by this routine) materials will only be duplicated once. 
                # This prevents many many copies of the same material
                
                # Does the user want us to make new material copies when child cutaway shaders are added
                #s=""
                #for k in duplicated_material_name_dict.keys(): s += k + ", "
                #print("duplicate enter", matslot.material.name, s)
                
                material_already_duplicated = matslot.material.name in duplicated_material_name_dict.keys()
                
                # Does the user want us to make new material copies when child cutaway shaders are added
                # make_duplicate_copy is hardwired to true for the moment 
                if (make_duplicate_copy):
                    # Yes they do.
                    # Has this material already been duplicated in call to add_child_nodes(...)
                    if (material_already_duplicated == False):
                        # no, so duplicate the materail
                        old_name = matslot.material.name +""
                        # Before making a copy of the material - prevent individual pynodes from triggering their node copy 
                        new_mat = matslot.material.copy()
                        # DSW: xxx don't append a new fancy name str
                        #new_mat.name = matslot.material.name  + ".cutshdr" #"_cutshdr"         # blender will ensure that a unique id is appended to the name
                        obj.material_slots[matslot_index].material = new_mat
                        # allow the new material to be referenced using the name of the old material
                        duplicated_material_name_dict[old_name] = new_mat
                    else:
                        #yes, get a reference to the recently duplicated material
                        new_mat = duplicated_material_name_dict[matslot.material.name]
                        obj.material_slots[matslot_index].material = new_mat
                        
                        # There is no need to create a new cutaway shader - we just re-used one that was created earlier
                        # so continue to the next object
                        # DSW check - does a driver have to be added to the effect mix?
                        continue
                    
                    
                    node_tree = new_mat.node_tree
                    outmat_node  = node_tree.nodes["Material Output"]      # there can be only one ... [outMat node]
                    surface_skt =  outmat_node.inputs["Surface"]
                    surface_skt_feeder_skt = surface_skt.links[0].from_socket

                # calculate the gap width between the output material node and its feeder node 
                #(this is currently ignoring and volume or displacement nodes that may be connected
                gap = abs(surface_skt_feeder_skt.node.location.x - outmat_node.location.x)
                required_gap_filler = cutaway_nodes_width - gap
                if required_gap_filler < 0:
                    required_gap_filler = 0
                    
                # move the Material Output node to the right to make way for the cut away shader
                outmat_node.location.x +=  required_gap_filler
                
                # add in a new cut away shader py and osl node.
                child_py_node = node_tree.nodes.new('CutAwayShaderNodeType')       
                child_osl_node_name =  child_py_node.osl_nodename_str             
                child_osl_node = node_tree.nodes[child_osl_node_name]       
                
                # line up the nodes so they're all pretty
                child_py_node.location = outmat_node.location
                child_py_node.location.x -= cutaway_nodes_width
                child_py_node.location.y -=NODE_Y_OFFSET
                
                child_osl_node.location = outmat_node.location
                child_osl_node.location.x -= cutaway_nodes_width /2
                
                node_tree.links.new(surface_skt, child_osl_node.outputs[0])                                 # Shader -> CutAwayShaderOut
                node_tree.links.new(child_osl_node.inputs[0], surface_skt_feeder_skt)                       # CutawayShaderIn ->  Bsdf_diffuseGreen             
                
                # let the new  py node know that it is a child node, and let it know who its parent material and object is.
                # todo: looks like there is redundancy in the lines below. see if mat_name_str and py name str is over done.
                self.append_child_unique_pynode_id_to_parents_master_child_dict(child_py_node)              #doubler  see zzzzz above for #doubleo
                child_py_node.make_a_child_node(parent_py_node_unique_id_str)                               #doublerx
                self.copy_parent_settings_to_child(child_py_node)
                
                # This allows key frames added to the parent node's mixEffectFactor to be applied to
                # all child nodes. Blenders driver system will handle the task of keeping track of
                # the child nodes. Note - many methods were tried to get key frames from the parent mixEffectFactor
                # to copy over to the child nodes (along with several other properties). These would work when 
                # properties were chnged directly by the user (using the node sliders) but did not work when
                # the property was key framed!
                # This technique could also be applied to other properties that need to be copied to child nodes.
                # This could be alot faster than the current method of iterating over each material (until be find the child nodes)
                # DSW: Put in 'todo' list 
                #self.addMixFactorDriver(child_py_node.osl_nodename_str)
                
                    
                    
                    
        # restore selection and active obj
        bpy.ops.object.select_all(action='DESELECT')
        for obj in selected_obj_list:
            obj.select = True
           
        bpy.context.scene.objects.active = save_active_obj
                
    # The remove child nodes from_selected objects button (cas_btn.remove_child_nodes_from_selected) has been pressed and this function called.           
    def remove_child_nodes_from_selected(self):
        self.carry_out_action_on_this_parents_child_nodes_b(action_str = 'REMOVE_CHILD_NODES')
      

    # A simple name 'override' of the function carry_out_action_on_this_parents_child_nodes_b(...).
    # This allows us to specify our own list of child or parent nodes to iterate over.
    def carry_out_action_on_child_nodes_b( self, 
                                         action_str = '', 
                                         param1 = None,                                         # optional parameter to feed to action. (action specific)
                                         param2 = None,                                         # optional parameter to feed to action. (action specific)
                                         child_object_override_list = None,                     # use this obj list instead of the child obj list
                                         allowed_to_clean = True):                              # clean unused/nonexistent child objs from child obj list
        
        return self.carry_out_action_on_this_parents_child_nodes_b(action_str, param1, param2, child_object_override_list, allowed_to_clean)  
    
    
    
    # There are several situations where we need copy some parent cutaway shader parameter to the child cutaway shader nodes.
    # This involves iterating over every child object of the parent shader object.
    # For the child object, we must check every material slot, every node tree and every node to look for child cutaway shader nodes to carry out the required action.
    # Because the code to carry out the looping and checking is very similar for all child node actions, this routine:
    # - Finds all child nodes belonging to the the parent.
    # - Carries out the desired action.
    # - Cleans child objects from the parents 'childlist_str' (a comma delimited list string of child object names) if the child object is not found (e.g. because the user deleted it).
    #   Note: The child object names do not use the obj.name property - as this can be altered by the user. A unique id (assigned by the parent node) is used instead.
    #         As a side note: Special code is used to trap situations where the user copies an object (and it's materials). When this situation is encountered, a new unique id is assigned to the nre child object.
    # - An optional child_object_override_list (string) list can be provided to this routine. 
    #   This allows an arbitrary set of objects in the scene (containing cutaway shaders) 
    #   doubler
    def carry_out_action_on_this_parents_child_nodes_b(self, 
                                                     action_str = '', 
                                                     param1 = None,                             # optional parameter to feed to action. (action specific)
                                                     param2 = None,                             # optional parameter to feed to action. (action specific)
                                                     child_object_override_list = None,         # use this obj list instead of the child obj list
                                                     allowed_to_clean = True):                  # clean unused/nonexistent child objs from child obj list
        return_bool = False
        # don't do if we are a child node 
        if (self.node_is_parent == False):
            return return_bool
        
        clean_child_node_keys_that_no_longer_exist_list = []
        
        # iterate through all the child keys of this parent node
        for key_str in self.keys():                                         # FOR LOOP 1
            # not all keys belong to the 'parent's node unique id' (pnuid)
            # so check that pnuid is in the key name
            if key_str.find("pnuid") > -1:
                # extract the child node unique id str from the dict
                child_pynode_unique_id_str = self[key_str]
                # iterate through all materials and nodes to find the child node we're after
                found_child = False
                for mat in bpy.data.materials:                              # FOR LOOP 2  
                    if mat.use_nodes:
                        for child_py_node in mat.node_tree.nodes:           # FOR LOOP 3  
                            #if child_py_node.name.find("Cutaway Shader") != -1:
                            if "Cutaway Shader" in child_py_node.name:
                                if child_pynode_unique_id_str == self.get_unique_pynode_id_str__create_if_neccessary(child_py_node):
                                    # child_py_node is actually a child py node
                                    found_child = True
                                    osl_node = mat.node_tree.nodes[child_py_node.osl_nodename_str]
                                    # no need to keep iterating through the mat.node_tree.nodes:
                                    break                                   # Exit FOR LOOP 3 - no need to look through more nodes
                        if found_child == True:
                            break                                           # Exit FOR LOOP 2 - no need to look through more materials
                             
                                    
                # did we find the child node in any of the materials?        
                if found_child == False:
                    # no we didn't. 
                    # The child pynode no longer exists (the user may have deleted the node of the material) - so 
                    # remove the key from this parent node's record of child nodes at the end of this operation.
                    # (we can't remove it now because we're iterating over the keys) 
                    #print("appending to erase list", key_str)
                    clean_child_node_keys_that_no_longer_exist_list.append(key_str)

                    # continue to the next child node id in the key set
                    continue                                                # continue with  FOR LOOP 1 id child node not found

                # If we are here we have found a reference to the child pynode that matches child_pynode_unique_id_str
                # now it's time to carry out the action given by action_str
                 
                # Carry out child_node_action
                # *********************************************
                # SELECT_CHILD_OBJS
                # Done1
                # A Does not need child_py_node, or osl_node
                if (action_str == 'SELECT_CHILD_OBJS'):   
                    self.select_all_objects_using_this_unique_pynode_id(child_pynode_unique_id_str, False)
                    # continue looking through the keys of this parent node for more child node id str keys 
                    continue                                                # continue with  FOR LOOP 1
                
                # *********************************************
                # REMOVE_CHILD_NODES
                # Done1
                # B Needs child_py_node, or osl_node
                elif (action_str == 'REMOVE_CHILD_NODES'):
                    # only want to remove child nodes from selected objects
                    i = 0
                    obj_list , matslot_list = self.get_all_objs_using_pynode(child_pynode_unique_id_str)
                    for obj in obj_list:
                        if (obj.select):
                            # remove the reference to the child pynode from this parent
                            #key_name = 'pnuid'+child_pynode_unique_id_str
                            #if key_name not in parent_node.keys():
                            #del self["pnuid"+child_pynode_unique_id_str]
                            # check if below is correct - should it be more similar to the above?
                            if  child_pynode_unique_id_str in self:                                 # doubler
                                del self["pnuid"+child_pynode_unique_id_str]

                            # get the OSL input feeder socket
                            osl_shaderin_skt = osl_node.inputs["ShaderIn"]
                            osl_shaderin_skt_feeder_skt = osl_shaderin_skt.links[0].from_socket     # src: the feeder socker

                            # get the OSL output fed socket
                            osl_shaderout_skt = osl_node.outputs["CutAwayShaderOut"]
                            osl_shaderout_skt_fed_skt = osl_shaderout_skt.links[0].to_socket        # dest: the fed socket
                            
                            # Before the OSL node is removed - re link the shaders each side of it
                            mat.node_tree.links.new(osl_shaderout_skt_fed_skt, osl_shaderin_skt_feeder_skt)
                            
                            # A Hack to get the shaded object to re-draw (this will prevent the deleted cut away shader from 'hanging around')        
                            matslot_list[i].material.use_nodes = False      # I assume this triggers the dependancy graph to force a 3D rendered scene re-draw.
                            matslot_list[i].material.use_nodes = True
                          
                            # remove the cutaway child_py_node and osl_node
                            nodes = osl_node.id_data.nodes
                            nodes.remove(osl_node)
                            nodes.remove(child_py_node)
                            
                            # now tidy up
                            # cutaway_nodes_width = 100
                            # outmat_node.location.x -=  cutaway_nodes_width
                            
                            # We can break out of the obj in obj_list loop because even though many objects may have been selected, this pynode is
                            # only in one material. Once the pynode and osl node have been removed from the material, there is no need to remove them
                            # again for other objects (since they already have been removed)
                            break
                        i += 1
                            
                
                # *********************************************
                # CLEAN_CHILD_LIST   
                # Done1 
                # A Does not need child_py_node, or osl_node
                elif (action_str == 'CLEAN_CHILD_LIST'):
                    # All cleaning is done automatically. No further action
                    break
                
                # *********************************************
                # COPY_PARENT_SETTINGS_TO_CHILD
                # Done1
                # B Needs child_py_node, or osl_node
                elif (action_str == 'COPY_PARENT_SETTINGS_TO_CHILD'):
                    # This is a child - so copy our data over
                    #if (matslot.material not in material_covered_list):
                    #    material_covered_list.append(matslot.material)
                    self.copy_parent_settings_to_child(child_py_node)
                 
                # *********************************************
                # COPY_NEW_CUTAWAY_PLANE_SETTINGS_TO_CHILD   
                # param1 = new cut away plane name str
                # param2 = XML rim segment data (describes all the edges of the cutaway plane to the OSL shader as an XML string) 
                # Done1
                # B Needs child_py_node, or osl_node     
                elif (action_str == 'COPY_NEW_CUTAWAY_PLANE_SETTINGS_TO_CHILD'):
                    child_py_node.set_child_cutaway_plane(param1, param2)
                 
                # *********************************************
                # COPY_RECT_CIRCULAR_SETTINGS_TO_CHILD 
                # Done1
                # B Needs child_py_node, or osl_node      
                elif (action_str == 'COPY_RECT_CIRCULAR_SETTINGS_TO_CHILD'):
                    child_py_node.set_child_rect_circular_settings(self.rectangular_circular_int, self.cutaway_image_path_and_name_str)
                    
                
                # *********************************************
                # COPY_INVERT_CUTAWAY_BOUNDS_TO_CHILD 
                # Done1
                # B Needs child_py_node, or osl_node  
                elif (action_str == 'COPY_INVERT_CUTAWAY_BOUNDS_TO_CHILD'):
                    child_py_node.copy_invert_cutaway_bounds_to_child(self.invert_cutaway_bounds_prop)
                    
                # *********************************************
                # COPY_FADEDIST_AND_SHARPNESS_TO_CHILD
                # Done1
                # B Needs child_py_node, or osl_node  
                elif (action_str == 'COPY_FADEDIST_AND_SHARPNESS_TO_CHILD'):
                    child_py_node.copy_fadedist_and_sharpness_to_child(self.edge_fade_distance_float_prop, self.edge_fade_sharpness_float_prop)
                    
                # *********************************************
                # COPY_NEW_ORIGIN_TO_CHILD 
                # Done1
                # B Needs child_py_node, or osl_node                                         
                elif (action_str == 'COPY_NEW_ORIGIN_TO_CHILD'):
                    # This is a child obj- so copy our data over
                    osl_node = child_py_node.id_data.nodes[child_py_node.osl_nodename_str]
                    
                    # param1 equals the  origin_offset_vec
                    osl_node.inputs["OriginOffset"].default_value = param1 
                    
                # *********************************************
                # COPY_MIX_FACTOR_TO_CHILD  
                # Done1
                # B Needs child_py_node, or osl_node       
                elif (action_str == 'COPY_MIX_FACTOR_TO_CHILD'):
                    child_py_node.set_cutaway_mix_float(self.effectmix_float)
                    
                # *********************************************
                # CHECK_IF_VALID_CHILD_NODE_EXITS 
                # Done1
                # A Does not need child_py_node, or osl_node    
                elif (action_str == 'CHECK_IF_VALID_CHILD_NODE_EXITS'):
                    # This is a child - so return true (no need to carry out further checking)
                    return True
                                       
        # Clean out any object names form the child list if the objects couldn't be found                                
        if  ((len(clean_child_node_keys_that_no_longer_exist_list) > 0) and allowed_to_clean):
            for child_pynode_key_str_to_remove_from_this_parent in clean_child_node_keys_that_no_longer_exist_list:
                # remove the key that had no corresponding child pynode
                if child_pynode_key_str_to_remove_from_this_parent in self:
                    #print("removing", child_pynode_key_str_to_remove_from_this_parent)
                    del self[child_pynode_key_str_to_remove_from_this_parent]
            
        return return_bool                            
    
        
    # Iterate through all the ojects in the scene. If they are child to this parent node then select them  
    # Called after the "Select All" button pressed in the draw method
    def select_all_child_nodes(self):
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        self.carry_out_action_on_this_parents_child_nodes_b(action_str = 'SELECT_CHILD_OBJS')

            
    #doubler for select_all_parents
    # Called after an operator button press on the parent pynode.
    # Select all objects that use the material that contains this node
    def select_all_objects_using_this_parent_node(self):
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        
        # Get our (parent) pynode's unique id
        parent_unique_pynode_id_str = self.get_unique_pynode_id_str__create_if_neccessary(self)
        
        # Get a list of the objects in the scene that use this pynode.
        obj_list, matslot_list = self.get_all_objs_using_pynode(parent_unique_pynode_id_str)
        
        # Select all objects in the scene that use this pynode.
        # (Enable the layers the object is on if needed)
        for obj in obj_list:
            for i in range (len(bpy.context.scene.layers)):
                if obj.layers[i] == True:
                    bpy.context.scene.layers[i] = True
                    break
            obj.select = True
            
    def select_all_objects_using_this_unique_pynode_id(self, unique_pynode_id_str, jump_node_editor_to_active_material_bool):
        # Get a list of the objects in the scene that use this pynode.
        obj_list, matslot_list = self.get_all_objs_using_pynode(unique_pynode_id_str)

        # No objects with using a material with the pynode of the given unique id was found.
        # exit with a False (This is probably an orphaned child node)
        if (len(obj_list) == 0):
            return False
        
        if (jump_node_editor_to_active_material_bool):
            bpy.context.space_data.pin = False
            
        # we need to be in object mode to do this work
        # save the area type -- should be node editor since a pynode button was pressed.
        # the cursor bpy ops only work from the 3d view context. So, switch to this.
        bpy.ops.object.mode_set(mode='OBJECT')
        original_areatype = bpy.context.area.type
        bpy.context.area.type = "VIEW_3D"
        

        if (jump_node_editor_to_active_material_bool):
            saved_3d_layers_setting_list = self.save_3d_view_layer_settings(bpy.context.space_data.layers)
            bpy.context.space_data.layers = [True] * 20

        #bpy.ops.object.select_all(action='DESELECT')  
        
        # Select all objects in the scene that use this pynode.
        # Enable layers the object is on if they are disabled
        for obj in obj_list:
            for i in range (len(bpy.context.scene.layers)):
                if obj.layers[i] == True:
                    bpy.context.scene.layers[i] = True
                    break
            obj.select = True
            # make the node editor jump to the objects active material. (Used for child node button "Jump to Parent Node"
            if(jump_node_editor_to_active_material_bool):
                bpy.context.scene.objects.active = obj
                self.restore_3d_view_layer_settings(bpy.context.space_data.layers, saved_3d_layers_setting_list)
                
        # switch back to the users original context
        bpy.context.area.type = original_areatype
        
        # We found object(s) using a material with the pynode of the given unique id - so return true
        return True
         
           
    # The user has clicked the "Jump to Parent Node" button on a child pynode.
    # Change the node view to show the parent pynode
    # If this is called we are a child node
    def jump_to_parent_node(self):  
        if (self.this_childs_parent_pynode_unique_id_str != ''):
            found_parent_bool = self.select_all_objects_using_this_unique_pynode_id(self.this_childs_parent_pynode_unique_id_str, True)   # True => show (jump to) parent material tree node
            
            if (found_parent_bool == False):
                # Either the parent material has been deleted, or no object is using the parent material.
                # This triggers a message in the child pynode recommending the user UNLINKs this orphaned node
                self.orphaned_child_node_bool = True
            else:
                self.orphaned_child_node_bool = False
                # Ensure the the parent knows about us (in case we were cleaned from its keys)
                # If we are already in the keys - then there is no change
                parent_node = self.get_parent_pynode()  
                if (parent_node != None):
                    parent_node.append_child_unique_pynode_id_to_parents_master_child_dict(self)

         
    # The user has clicked the "Select Parent Object" button on a child pynode.
    # Find an object that uses the material that contains the parent py node. 
    # Enable the screen layer(s) containing this object and select it so the user can see the obj in the viewer (and also the node tree if a node tree screen is showing)    
    # If this is called we are a child node 
    def select_parent_node(self): 
        # if the parent id exists, then select all objs that use the parent node in their material setup
        if (self.this_childs_parent_pynode_unique_id_str != ''):
            found_parent_bool = self.select_all_objects_using_this_unique_pynode_id(self.this_childs_parent_pynode_unique_id_str, False) # False => don't show (jump to) parent material tree node
            
            
            if (found_parent_bool == False):
                # Either the parent material has been deleted, or no object is using the parent material.
                # This triggers a message in the child pynode recommending the user UNLINKs this orphaned node
                self.orphaned_child_node_bool = True
            else:
                self.orphaned_child_node_bool = False
                # Ensure the the parent knows about us (in case we were cleaned from its keys)
                # If we are already in the keys - then there is no change
                parent_node = self.get_parent_pynode()  
                if (parent_node != None):
                    parent_node.append_child_unique_pynode_id_to_parents_master_child_dict(self)
                
            
    # The user has pressed the select all parents in the scene button - we are a parent node
    def select_all_parents_in_scene(self):
        # we need to be in object mode to do this work
        bpy.ops.object.mode_set(mode='OBJECT')
                
        # save the area type -- should be node editor since a node editor button was pressed.
        original_areatype = bpy.context.area.type
    
        # the cursor bpy ops only work from the 3d view context. So, switch to this.
        bpy.context.area.type = "VIEW_3D"
        saved_3d_layers_setting_list = self.save_3d_view_layer_settings(bpy.context.space_data.layers)
        bpy.context.space_data.layers = [True] * 20
        
        bpy.ops.object.select_all(action='DESELECT')
        for obj in bpy.context.scene.objects:
            obj_selected = False
            for matslot in obj.material_slots:
                if (matslot.material != None):
                    if (matslot.material.node_tree != None):
                        for node in matslot.material.node_tree.nodes:
                            #if node.name.find("Cutaway Shader") > -1:
                            if "Cutaway Shader" in node.name:
                                if node.node_is_parent:
                                    obj_selected = True
                                    for i in range (len(bpy.context.scene.layers)):
                                        if obj.layers[i] == True:
                                            bpy.context.scene.layers[i] = True
                                            bpy.context.space_data.layers[i] = True
                                            break
                                    break  # (break for node)
                if obj_selected:
                    break # break for matslot
            obj.select = obj_selected
        
        
        self.restore_3d_view_layer_settings(bpy.context.space_data.layers, saved_3d_layers_setting_list)
             
        # switch back to the users original context
        bpy.context.area.type = original_areatype
      

        
    # The user has pressed the "Select all Objects using this child shader" button
    # We are a child node    
    def select_all_objects_using_this_child_node(self):
        id_str = self.get_unique_pynode_id_str__create_if_neccessary(self)
        self.select_all_objects_using_this_unique_pynode_id(id_str, False) 
                   
    def remove_all_cut_away_shader_nodes(self):
        # iterate over all materials and all treenodes and all nodes until we find our parent Cutaway Shader pynode.
        for mat in bpy.data.materials:
            if mat.use_nodes:
                for node in mat.node_tree.nodes:
                    #if node.name.find("Cutaway Shader") != -1:
                    if "Cutaway Shader" in node.name:
                        pynode = node
                        # remove this shader and its OSL node
                        # get the OSL input feeder socket
                        if pynode.osl_nodename_str in pynode.id_data.nodes.keys():
                            osl_node = pynode.id_data.nodes[pynode.osl_nodename_str]
                            if osl_node != None:
                                osl_shaderin_skt = osl_node.inputs["ShaderIn"]
                                if (len(osl_shaderin_skt.links) >0):
                                    osl_shaderin_skt_feeder_skt = osl_shaderin_skt.links[0].from_socket     # src: the feeder socker

                                    # get the OSL output fed socket
                                    osl_shaderout_skt = osl_node.outputs["CutAwayShaderOut"]
                                    if (len(osl_shaderout_skt.links) >0):
                                        osl_shaderout_skt_fed_skt = osl_shaderout_skt.links[0].to_socket        # dest: the fed socket
                                        
                                        # Before the OSL node is removed - re link the shaders each side of it
                                        mat.node_tree.links.new(osl_shaderout_skt_fed_skt, osl_shaderin_skt_feeder_skt)
                                    
                              
                                # remove the cutaway child_py_node and osl_node
                                nodes = osl_node.id_data.nodes
                                nodes.remove(osl_node)
                                nodes.remove(pynode)
                        
                        

    # Called from a button: 
    # A new cut away plane is being added to the scene, and the user wants a helper 
    # Red/Green material (Green is the cutaway side. Red is the 'do not cutaway' side).
    def create_cutawayplane_material(self):
        name_compat = 'cutawayPlaneHelperMat'
        material = None
        overwrite_node_tree = True
        for mat in bpy.data.materials:
            if mat.name == name_compat and overwrite_node_tree:
                material = mat
        if not material:
            material = bpy.data.materials.new(name=name_compat)

        material.use_nodes = True
        node_tree = material.node_tree
        out_node = self.clean_node_tree(node_tree)
        
        bsdf_diffuseGreen = node_tree.nodes.new('ShaderNodeBsdfDiffuse')
        bsdf_diffuseRed= node_tree.nodes.new('ShaderNodeBsdfDiffuse')
        geom = node_tree.nodes.new('ShaderNodeNewGeometry')
        mix = node_tree.nodes.new('ShaderNodeMixShader')
        
        # Naming the mix node allows us to identify this as a 'helper' material
        # We use this to prevent the auto adding of cutaway shader ChildNodes to the cut away plane.
        mix.name = 'cutAwayMix'
        
        node_tree.links.new(out_node.inputs[0], mix.outputs[0])             # Shader -> Surface
        node_tree.links.new(mix.inputs[0], geom.outputs[6])                 # Backfacing -> Fac
        node_tree.links.new(mix.inputs[1], bsdf_diffuseGreen.outputs[0])    # BSDF -> Shader
        node_tree.links.new(mix.inputs[2], bsdf_diffuseRed.outputs[0])      # BSDF -> Shader
        bsdf_diffuseGreen.inputs[0].default_value = (0.0, 0.80, 0.169, 1.0)
        bsdf_diffuseRed.inputs[0].default_value = (1.0, 0.0, 0.0, 1.0)

        self.auto_align_nodes(node_tree)
        return material
    
    
    def find_modifier_for_active_obj(self, modifier_name_str):
        found = False
        for i, modifier in enumerate(bpy.context.object.modifiers):
            if (modifier.name == modifier_name_str):
                found = True
                break
        
        if (found):
            return i
        else:
            return -1
        
        
    def find_modifier(self, modifier_name_str, obj):
        found = False
        for i, modifier in enumerate(obj.modifiers):
            if (modifier.name == modifier_name_str):
                found = True
                break
        if (found):
            return i
        else:
            return -1

    
    #doubler
    def get_all_objs_using_pynode(self, pynode_unique_id_str):
        obj_list = []
        matslot_list = []
        for obj in bpy.context.scene.objects:
            foundobj = False;
            for matslot in obj.material_slots:
                if (matslot.material != None):
                    if matslot.material.use_nodes:
                        for node in matslot.material.node_tree.nodes:
                            #if node.name.find("Cutaway Shader") != -1:
                            if "Cutaway Shader" in node.name:
                                node_unique_id_str = self.get_unique_pynode_id_str__create_if_neccessary(node)
                                if pynode_unique_id_str == node_unique_id_str:
                                    # We have found a pynode (and hence material) that matches the one passed to us as a param
                                    # add this object to the list and move on, there is no need to check the rest of the 
                                    # materials this obj uses - as we have added the obj to the list).
                                    obj_list.append(obj)
                                    matslot_list.append(matslot)
                                    foundobj = True
                                    break  # node loop
                if foundobj == True:
                    break # matslot loop  
        return obj_list, matslot_list
    

    # debug helper 
    #def reset_wm_counters(self):
    #    wm = bpy.data.window_managers[0]
    #    wm['pynode_unique_id_counter_int'] = 0  
        
    def check_unique_pynode_id_exists__create_if_neccessary(self, pynode):
        # Check if the unique_pynode_id_int has been defined
        if 'unique_pynode_id_str' not in pynode.keys():
            # No it hasn't - so define it
            pynode['unique_pynode_id_str'] = '0'
            
        # Check if the global id counter has been defined
        if 'pynode_unique_id_counter_int' not in bpy.context.scene.keys():
            bpy.context.scene['pynode_unique_id_counter_int'] = 0
            
    # Get the unique idstr that is assigned to every cut away shader pydnode.
    # If the shader (for some reason) doesn't have a unique id - then create one.     
    def get_unique_pynode_id_str__create_if_neccessary(self, pynode, force_assignment_bool = False):
        # Check that the pynode_unique_id_counter and unique_pynode_id_str exist - create them if they don't
        self.check_unique_pynode_id_exists__create_if_neccessary(pynode)
        
        #unique_id_str = pynode.unique_pynode_id_str
        # if needed, assign a unique id to this cut away shader pynode, and increase the unique counter
        if force_assignment_bool or pynode['unique_pynode_id_str'] == '0':
            pynode['unique_pynode_id_str'] = str(bpy.context.scene['pynode_unique_id_counter_int'])
            bpy.context.scene['pynode_unique_id_counter_int'] += 1
            
        # return the pynode unique id    
        return pynode['unique_pynode_id_str']
        
    def define_global_auto_update_child_nodes_on_frame_change_bool_if_neccessary(self):
        # Check if global_auto_update_child_nodes_on_frame_change_bool has been defined
        if 'global_auto_update_child_nodes_on_frame_change_bool' not in bpy.context.scene.keys():
            bpy.context.scene['global_auto_update_child_nodes_on_frame_change_bool'] = True
        
        
    def get_global_auto_update_child_nodes_on_frame_change_bool_create_if_neccessary(self):
        # Check that the global_auto_update_child_nodes_on_frame_change_bool exists - create them if they don't
        self.define_global_auto_update_child_nodes_on_frame_change_bool_if_neccessary()
        return bpy.context.scene['global_auto_update_child_nodes_on_frame_change_bool']
        
    def set_global_auto_update_child_nodes_on_frame_change_bool_create_if_neccessary(self, value_bool):
         # Check that the global_auto_update_child_nodes_on_frame_change_bool exists - create them if they don't
        self.define_global_auto_update_child_nodes_on_frame_change_bool_if_neccessary()
        bpy.context.scene['global_auto_update_child_nodes_on_frame_change_bool'] = value_bool
        
        

            
    #double1r
    # The unique id of the given (child) pynode is added to the parents keys.
    # The key format is: 'pnuidX', where X represents the integer id (in string format) e.g.  pnuid1  , pnuid3895 ... etc. 
    # pnuid stands for pynode unique id.
    # If the child pynode does not have a unique id yet - one will be created
    # If the child pynode unique id has already been added as a key -- no change is made
    # If this is called, we are a parent node.
    def append_child_unique_pynode_id_to_parents_master_child_dict(self, child_pynode):
        parent_node = self
        
        # If the child pynode does not already have a unique id, one will be created
        child_pynode_unique_id_str = self.get_unique_pynode_id_str__create_if_neccessary(child_pynode)
    
        key_name = 'pnuid'+child_pynode_unique_id_str
        if key_name not in parent_node.keys():
            #print("child pynode added to parent keys: ", child_pynode_unique_id_str)
            parent_node[key_name] = child_pynode_unique_id_str

    

    # Called from button: The user wants to create a new cutaway material
    # The user wants to add a thickness modifier to the selected mesh and create an inner mesh shader
    # steps
    # - 1) create the solidify modifier
    # - 2) create the new material for the inner mesh
    # - 3) Add the new material to the object
    # - 4) set the offset material index
    # - 5) link the new inner mesh node as the child of the node where the button was pressed.
    
    # This helper will:
    #   -  add a thickness modifier to the active object iff that object uses this material
    #   -  add a child material (an inner mesh cutaway shader) if there isn't one already. 
    def add_inner_solidifier_mesh_and_material(self):
        # 1) create the thickness modifier
        # get the active object in the scene (if there is one)
        active_obj_save = bpy.context.scene.objects.active
        if (active_obj_save == None):
            return
        
        # Get our (parent) pynode's unique id
        parent_unique_pynode_id_str = self.get_unique_pynode_id_str__create_if_neccessary(self)
        
        # Get a list of the objects in the scene that use this pynode.
        obj_list, matslot_list = self.get_all_objs_using_pynode(parent_unique_pynode_id_str)
        
        # if the active object does not use a cutaway shader - then exit
        # DSW: xxx investigate why secondary material not always added
        if (active_obj_save not in obj_list):
            return
        
        # save the active material to prevent the node editor from jumping to the child node
        # note: may get a bug if the node editor is pinned - and the active index is not the one we think it is.
        # however -- if the node is pinned - we don't have the jumping problem any way.
        save_matslot_index = active_obj_save.active_material_index 
        
        # If the object doesn't have a solidify modifier, then add one
        index = self.find_modifier_for_active_obj("Solidify")
        if (index == -1): 
            bpy.ops.object.modifier_add(type='SOLIDIFY')
             
        # set up the solidify modifier. It creates the objects 'inner mesh'.     
        bpy.context.object.modifiers["Solidify"].thickness = 0.07
        bpy.context.object.modifiers["Solidify"].use_rim = False
        

        # 2a) Check if this parent node already has a child. 
        has_valid_child_mat_bool = False
        material = None
        # DSW: xxx commented out because it used the old id name str scheme. Look to see if it needs to be updated.
#        if (self.is_a_linked_parent_node()):  
#            # This node already has a child node (or nodes) , so no need to create a new material -- we can use the existing one
#            # need to check if there is already an inner mesh material in this object matslots
#            child_obj_name_list = []
#            child_obj_name_list.append(self.get_cshader_obj_idstr(active_obj_save))
#            self.append_to_child_objname_liststr(active_obj_save);                                                                        #doubleo  see ttttt below for #doubleor                                                                  
#            has_valid_child_mat_bool =self.carry_out_action_on_child_nodes_b("CHECK_IF_VALID_CHILD_NODE_EXITS", 
#                                                                            None, None, 
#                                                                            child_obj_name_list, allowed_to_clean = False)
            
            
#            '''
#            obj_has_mat = False
#            for mat in active_obj_save.material_slots:
#                self.carry_out_action_on_child_nodes
#                # perform a full check to see if there is a child node with us as its parent
#                i = mat.name.find('child_mesh')
#                if (i > -1):
#                    material = mat
#                    break
#            '''
         
        if (has_valid_child_mat_bool == False):
            child_py_node = self.add_default_child_material_to_obj((0, 1, 1, 1), inner_mesh_bool = True)
            
            self.append_child_unique_pynode_id_to_parents_master_child_dict(child_py_node)                                    #doubler  see ttttt above for #doubleo
            

            # 5) Make this new material and its cutaway shader a child node
            child_py_node.make_a_child_node(parent_unique_pynode_id_str)        #doublerx
        
        bpy.context.scene.objects.active = active_obj_save
        
        # 4) Set the offset material index in the solidify modifer so the 'inner mesh' points to this new material.
        #    For the selected object, we need to find which slot our newly created material is in
        for i, slot in enumerate(bpy.context.object.material_slots):
            # DSW: xxx material always == None at present. check this
            if slot.material == material:
                # i = the material slot offset number
                break
        bpy.context.object.modifiers["Solidify"].material_offset = i   
        
        
        # Add the active object to the child node list
        self.copy_parent_settings_to_all_child_nodes()
        
        # preserve the state of the original active object
        # This will stop the node tree view from jumping to the cutaway plane
        bpy.context.scene.objects.active = active_obj_save
        active_obj_save.active_material_index = save_matslot_index
    
    # Create a new diffuse material and add it to bpy.context.object's material slot
    # This routine is called if either:
    #       - The user has just selected the "solidify' option on the pynode. This new material will become the material referenced by the solidfy modifier
    # or    - The user wants to add child shader nodes to the selected object(s) -- but these nodes do not have any materials yet.
    # Input params: material color
    #               inner_mesh_bool = true  => material name = current shader's material name + '_cutAwayShader_solidifier_material'
    #               inner_mesh_bool = false => material name = current shader's material name + '_cutAwayShader_material'
    # Returns:      The cutaway_pynode of the new material.
    #
    def add_default_child_material_to_obj(self, mat_color, inner_mesh_bool = False):
        # 2b) create the new node based material. This will be applied to the "inner mesh" as a child cutaway node
        mat_name = "cutaway_shader_material"
        
        material = bpy.data.materials.new(name=mat_name)
        material.use_nodes = True
        
        # strip all the nodes out of the new (default) nodetree except the output
        node_tree = material.node_tree
        out_node = self.clean_node_tree(node_tree)
        
        # add the new INNER cutaway mesh shaders 
        bsdf_diffuseGreen = node_tree.nodes.new('ShaderNodeBsdfDiffuse')                                # - a default green inner sahder
        cutaway_py_node = node_tree.nodes.new('CutAwayShaderNodeType')                                  # - a the py_cutaway node  
        self.get_unique_pynode_id_str__create_if_neccessary(cutaway_py_node)                            # create a new unique id for the new  cutaway_py_node
        osl_node_name =  cutaway_py_node.osl_nodename_str             
        osl_node = node_tree.nodes[osl_node_name]                                                       # - an OSL cutaway node
        
        # set to cyan color (R, G, B, A) = (0, 1, 1, 1)
        bsdf_diffuseGreen.inputs[0].default_value = mat_color #(0, 1, 1, 1)   
        
        # link up the nodes
        node_tree.links.new(out_node.inputs[0], osl_node.outputs[0])             # Shader -> CutAwayShaderOut
        node_tree.links.new(osl_node.inputs[0], bsdf_diffuseGreen.outputs[0])    # CutawayShaderIn ->  Bsdf_diffuseGreen             

        # make the node layout all pretty
        self.auto_align_nodes(node_tree)
        cutaway_py_node.location[0] -= 125 #125
    
        #3) add the new material to the  object
        obj = bpy.context.object
        bpy.ops.object.material_slot_add()
        obj.material_slots[obj.material_slots.__len__() - 1].material = material
        return cutaway_py_node
    
    '''
    # If the default child material exists, it is added to the active object (we must be in the right context)
    # and the py_node is returned. If not found, None is returned
    def set_default_child_material_to_object(self):
        #name_compat = 'cutawayPlaneHelperMat'
        the_mat_idstr = self.get_mat_idstr()
        py_node = None
        material = None
        # does the default child mesh exist yet
        for mat in bpy.data.materials:
            if ((mat.name.find("_default_child_mesh") != -1) and (mat.name.find(the_mat_idstr) != -1)): #<==== no longer using this str: "_default_child_mesh")
                # Yes. The default child mesh exists
                material = mat
                # If the user hasn't tampered with it -- we should find the py_node for the default child material
                if(material.use_nodes):
                    nodes = material.node_tree.nodes
                    if ((self.py_nodename_str in nodes.keys()) and (self.osl_nodename_str in nodes.keys())):
                        # The default py_node exists. This default material is OK to use.
                        # make a note of the py_node, and set our object to use this material
                        py_node = nodes[self.py_nodename_str]
                        obj = bpy.context.object
                        bpy.ops.object.material_slot_add()
                        obj.material_slots[obj.material_slots.__len__() - 1].material = material
                break
            
        return py_node 
 
    ''' 

    # < Node layout helper functions >
    # node helper function from Import Planes by xxx
    def get_input_nodes(self, node, nodes, links):
        # Get all links going to node.
        input_links = {lnk for lnk in links if lnk.to_node == node}
        # Sort those links, get their input nodes (and avoid doubles!).
        sorted_nodes = []
        done_nodes = set()
        for socket in node.inputs:
            done_links = set()
            for link in input_links:
                nd = link.from_node
                if nd in done_nodes:
                    # Node already treated!
                    done_links.add(link)
                elif link.to_socket == socket:
                    sorted_nodes.append(nd)
                    done_links.add(link)
                    done_nodes.add(nd)
            input_links -= done_links
        return sorted_nodes
    
    # Align the newly created nodes for the Red/Green material. This code is from Import Planes by xxx
    def auto_align_nodes(self,node_tree):
        x_gap = 300
        y_gap = 300
        nodes = node_tree.nodes
        links = node_tree.links
        to_node = None
        for node in nodes:
            if node.type == 'OUTPUT_MATERIAL':
                to_node = node
                break
        if not to_node:
            return  # Unlikely, but better check anyway...

        # Align the newly created nodes.
        def align(to_node, nodes, links):
            from_nodes = self.get_input_nodes(to_node, nodes, links)
            for i, node in enumerate(from_nodes):
                node.location.x = to_node.location.x - x_gap
                node.location.y = to_node.location.y
                node.location.y -= i * y_gap
                node.location.y += (len(from_nodes)-1) * y_gap / (len(from_nodes))
                align(node, nodes, links)

        align(to_node, nodes, links)    
    
    # Clear all the nodes from the tree. This cide is from Import Planes by 
    def clean_node_tree(self, node_tree):
        nodes = node_tree.nodes
        for node in nodes:
            if not node.type == 'OUTPUT_MATERIAL':
                nodes.remove(node)
        return node_tree.nodes[0]
    # < !Node layout helper functions >
    
    
    
    def update_child_node_rect_circular_settings(self):
        # don't do if we are a child node 
        if (self.node_is_parent == False):
            return
        self.carry_out_action_on_this_parents_child_nodes_b(action_str = 'COPY_RECT_CIRCULAR_SETTINGS_TO_CHILD')
    
    
    # Called by the parent node shader (i.e if this runs then we are a child node)
    # Set the mode to rectangular or circular
    def set_child_rect_circular_settings(self, rect_circ_int, image_path_name_str):
        oslNode = self.id_data.nodes[self.osl_nodename_str]
        oslNode.inputs["DrawMode_circular0_rectangular1"].default_value = rect_circ_int
        oslNode.inputs["cutAwayImg"].default_value = image_path_name_str
        self.rectangular_circular_int = rect_circ_int
        self.cutaway_image_path_and_name_str = image_path_name_str
        
    

    
    # Called from set Origin option buttons: 
    # Let the OSL shader know where the origin is. 
    # If the origin is at the center, the offset is (0,0,0).
    # If the origin is on an edge (for example) then the OSL shader can use the offset
    # from center to work out where the center of the cut away plane is.
    # This allows the user to scale the plane form any origin convenient position - while allowing the
    # OSL shader workout where the plane center (for location purposes) actually is.                   
    def update_parent_and_child_origins(self, origin_offset_vec): 
        #print("******************************************call test2")
        # set the offset origin for the parent's osl node
        parent_oslNode = self.id_data.nodes[self.osl_nodename_str]
        parent_oslNode.inputs["OriginOffset"].default_value = origin_offset_vec
        # set the offset origin for the child nodes
        self.carry_out_action_on_this_parents_child_nodes_b(action_str = 'COPY_NEW_ORIGIN_TO_CHILD', param1 = origin_offset_vec)
        

    '''
    # Finds all parents, and set their mode to auto too.
    def get_a_list_of_all_parents_nodes(self):
        parent_pynode_list = []
        for obj in bpy.context.scene.objects:
            obj_selected = False
            for matslot in obj.material_slots:
                if (matslot.material != None):
                    if (matslot.material.node_tree != None):
                        for node in matslot.material.node_tree.nodes:
                            #if node.name.find("Cutaway Shader") > -1:
                            if "Cutaway Shader" in node.name:
                                if node.node_is_parent:
                                    parent_pynode_list.append(node)
                                    break  # (break for node)
        return parent_pynode_list
     
    # All parent nodes should have the same  auto_refresh_child_nodes_after_frame_change_bool state
    # Find the first parent node that has a valid id (and that is not ourselves) and get a copy of its auto_refresh_child_nodes_after_frame_change_bool
    # This is called when out node is first instantiated.
    # Note should probably make the auto_refresh_child_nodes_after_frame_change_bool property a global/scene property.
    def get_auto_refresh_global_state(self):
        return_state = True;
        our_unique_id_str = get_unique_id_str(self)
        if (our_unique_id_str == "none"):
            our_unique_id_str = "notset"
            
        parentnode_list = self.get_a_list_of_all_parents_nodes()
        for parentnode in parentnode_list:
            parentnode_unique_id_str = get_unique_id_str(parentnode)
            if ((parentnode_unique_id_str != "none") and (parentnode_unique_id_str != our_unique_id_str)):
                return_state = parentnode.auto_refresh_child_nodes_after_frame_change_bool
                break

        return return_state
                
    def get_unique_id_str(node):
        id_str = "none"
        if "unique_pynode_id_str" in node.keys():
            id_str = node["unique_pynode_id_str"]
    
    '''
        
        

    # Called by button:
    # Used by external operators to access the cutaway plane so that it's mesh can be accessed.
    def get_cutawayPlane_NameStr(self):
        return self.cutAwayPlaneNameStr
    

    # Called by the child node if they want out
    # We must be a parent node if this routine is called (by the child node)
    # reset our child settings to let the user know that there is no child selected    
    def child_select_none(self):
        self.carry_out_action_on_this_parents_child_nodes_b('CLEAN_CHILD_LIST')   
        
    # Called by the child node if they want out
    # We must be a parent node if this routine is called (by the child node)
    # reset our child settings to let the user know that there is no child selected    
    def remove_child_node_from_parent(self):
        self.carry_out_action_on_this_parents_child_nodes_b('CLEAN_CHILD_LIST')   
        
    
    # Called by button: When the user presses the Unlink child Node button
    # We must be a child node if this routine is called
    # Tell the parent node that we are no longer a child. Set ourselves to a parent node.
    # This will allow the user access to all the full settings of the cutaway py node.   
    # We  are a child node if this routine is being run.
    def unlink_child(self):
        
        unique_pynode_id_str = self.get_unique_pynode_id_str__create_if_neccessary(self)
        
        # let the parent node know that we are bugging out
        parent_node = self.get_parent_pynode()  
        if (parent_node != None):
            key_name = 'pnuid'+unique_pynode_id_str
            if key_name in parent_node.keys():
                # remove the reference the parent has to this child node
                del parent_node[key_name]

        # Do all the usual setups for the new parent node 
        self.node_is_parent = True                                              # no longer a child
        self.this_childs_parent_pynode_unique_id_str == ''                      # no longer a child with a parent
        
        # Let the OSL shader know that this is an outer (parent) mesh. This will allow a rim to be drawn if needed
        oslNode = self.id_data.nodes[self.osl_nodename_str]
        oslNode.inputs["InnerMesh0_OuterMesh1"].default_value = 1               # 1 = outer (parent) mesh
        

    def vec_to_str(self, vec):
        retstr =  "{0:.4f}".format(vec[0]) + ',' 
        retstr += "{0:.4f}".format(vec[1]) + ',' 
        retstr += "{0:.4f}".format(vec[2])
        return retstr
    
    def vector_attribute(self, attr_name_str, vec):
        ret_str = attr_name_str + '="' + self.vec_to_str(vec) + '"'
        return ret_str 
    
    def float_attribute(self, attr_name_str, thefloat):  
        ret_str = attr_name_str + '="' +  "{0:.4f}".format(thefloat) + '"'
        return ret_str
    
    # Return the vertices of an edge loop in transversal order.
    # Note depending on the loop design, the return list may be ordered as clockwise, or anti clockwise.
    # There is no specific check as to which direction the return list will be.
    # The first vertex in the list will also be the last vertex. (this suits our purpose for this shader helper).
    def sort_edge_verts(self, bm, bm_edges):
        vertlist = [];
        firstedge = True;
        still_looping = True;
        
        if hasattr(bm.verts, "ensure_lookup_table"): 
            bm.edges.ensure_lookup_table()
            
        current_vert = bm_edges[0].verts[0]
        last_vert = current_vert
        vertlist.append(current_vert)
        
        while(still_looping):
            # get a list of edges connected to this vert
            edges = current_vert.link_edges
            
            # get the next vert in the loop
            for edge in edges:
                if ((edge.verts[0].co != current_vert.co) and (edge.verts[0].co != last_vert.co)):
                    last_vert = current_vert
                    current_vert = edge.verts[0]
                    break
                elif ((edge.verts[1].co != current_vert.co) and (edge.verts[1].co != last_vert.co)):
                    last_vert = current_vert
                    current_vert = edge.verts[1]
                    break
            # add the new vert to the list        
            vertlist.append(current_vert)
            
            # have we looped all the way around?
            if (current_vert == vertlist[0]):
                still_looping = False
         
        return vertlist
                

    # Send all the edge segments that make up the cutaway plane to the OSL shader.
    # Method:
    # Iterate through all the edges in the mesh, find their local co-ordinate center points.
    # send the data to the OSL shader in the format:
    #   - edge center co-ordinate (local - pre rotated, pre scaled co-ords)
    #   - edge normal (local - pre rotated, pre scaled co-ords)
    #   - the x and y components l lengths f the edge. (perhaps could end the Len and let OSL deal with this
    # just do a test with the standard 4 edge plane for starters
    # todo: this look like it can crash if the py_node is a child node and the screen area space selects all layers on the child node - but the screen space of the parent node still has layers deselected
    def update_rim_segment_data(self, cutaway_obj):
        # we need to be in object mode to do this work
        bpy.ops.object.mode_set(mode='OBJECT')
                    
        # the cursor bpy ops only work from the 3d view context. So, switch to this.
        #original_areatype = bpy.context.area.type
        bpy.context.area.type = "VIEW_3D"
        
        # Save the layers the the cutaway_obj is visible on (so we can restore these later)
        saved_obj_layer_settings_list = self.save_obj_layer_settings(cutaway_obj)
        
        # Make all layers enabled - so we can find the cut away plane (if it was on a disabled layer)
        cutaway_obj.layers = [True] * 20 
        

        # deselect all objects in the scene
        bpy.ops.object.select_all(action='DESELECT')
        
        # Set the cutaway plane as the selected, active object
        cutaway_obj.select = True
        bpy.context.scene.objects.active = cutaway_obj

        # we need to be in edit mode to do this work
        bpy.ops.object.mode_set(mode='EDIT')
        
        # crank up bmesh :-)
        bm = bmesh.from_edit_mesh(cutaway_obj.data) 
        if hasattr(bm.verts, "ensure_lookup_table"): 
            bm.verts.ensure_lookup_table()

        # calculate the center origin of the plane in local co-ordinates.
        x_axis = mathutils.Vector((1.0, 0.0, 0.0))
        y_axis = mathutils.Vector((0.0, 1.0, 0.0))
        z_axis = mathutils.Vector((0.0, 0.0, 1.0))
        
        rim_vert_data_str = '<R>'

        vert_list = self.sort_edge_verts(bm, bm.edges)
        for vert in vert_list:
            rim_vert_data_str += '<E'
            rim_vert_data_str +=  self.vector_attribute(' v', vert.co)
            rim_vert_data_str += ' />'
        rim_vert_data_str += '</R>'
        
        bm.free()
        
      
        # put back in object mode
        bpy.ops.object.mode_set(mode='OBJECT')
        
        oslNode = self.id_data.nodes[self.osl_nodename_str]
        oslNode.inputs["RimSegmentXMLData"].default_value = rim_vert_data_str
        
        #obj_layer_array
        self.restore_obj_layer_settings(cutaway_obj, saved_obj_layer_settings_list)
        #bpy.context.object.layers = array.fromlist(saved_obj_layer_settings_list)
        
        # restore the users layer enabled settings
        #bpy.context.scene.layers = saved_layer_settings_list
        
        # The returned data can also be used by the child nodes (if any) - so they don't have to re-calculate this info
        return rim_vert_data_str 


    def save_3d_view_layer_settings(self, layers_array_ref):
        saved_3d_layer_settings_list = []
        for layer_vis in layers_array_ref:
            saved_3d_layer_settings_list.append(layer_vis)
        return saved_3d_layer_settings_list
    
    def restore_3d_view_layer_settings(self, layers_array_ref, layers_settings_list):
        for i  in range (len(layers_settings_list)):
            layers_array_ref[i] =  layers_settings_list[i]   
       
    
    def save_obj_layer_settings(self, obj):
        saved_obj_layer_settings_list = []
        for layer_vis in obj.layers:
            saved_obj_layer_settings_list.append(layer_vis)
        return saved_obj_layer_settings_list
    
    def restore_obj_layer_settings(self, obj, restore_list):
        for i  in range (len(bpy.context.scene.layers)):
            obj.layers[i] =  restore_list[i]   
          

    @classmethod
    def poll(cls, context):
        return True
    
    def socket_value_update(self, context):
        #print("SOCKET VAL UPDATE")
        return

    
    # This pynode is being copied (either with ctrl-C, or by the material being duplicated)
    # We need to update the pynodes unique id.
    #   Note: There seems to be a Blender bug (or a bug in this code that confuses Blender) that causes this
    #   routine to be called after *ANY*  changes in the node tree (e.g. changing the diffuse slider).
    #   A 'work around' is to check the bpy.context.screen. If it is not None, then we are actually being duplicated.
    #   (This work around took quite some time to find!)
    def copy(self, original_pynode): 
        area = bpy.context.area
        if area == None:
            return

        copied = False
        if (area.type == "PROPERTIES"):
            copied = True
        elif (area.type == "NODE_EDITOR"):
            copied = True
            
        if (copied):
            #print("!!!!!!!!!!!!!!!!!!!!!!!!")
            #print("We have been copied.")
         
            # save the old pynode id and create a new uniqie if for this pynode.
            old_pynode_id = self.get_unique_pynode_id_str__create_if_neccessary(self)
            self['unique_pynode_id_str'] = '0'
            new_pynode_id = self.get_unique_pynode_id_str__create_if_neccessary(self)
            print(old_pynode_id, new_pynode_id)
            
            # if this pynode is a child node - then find the parent pynode -- and add ourselves to its child list.
            if (self.node_is_parent == False):
                # We are a child node.
                parent_py_node = self.get_parent_pynode()
                if (parent_py_node != None):
                    parent_py_node.append_child_unique_pynode_id_to_parents_master_child_dict(self)
                    
            else:
                #print("WE ARE A PARENT")
                # we are potentially a parent node with  child nodes in our list
                has_children_test = False
                for keystr in  self.keys():
                    if keystr.find("pnuid") > -1:
                        # there is at least one child node attached to this parent. No need to keep searching
                        has_children_test = True
                        break
                    
                # If this newly duplicated parent node has children, we must make the original pynod parent a child of us
                # (we cant have two master nodes dictating the child node settings)    
                if (has_children_test == True):
                    # Find the original parent node and make it a child of us.
                    print("DUPLICATED - HAS CHILDREN")
                    exit= False
                    for mat in bpy.data.materials:                                              # for loop A
                        if mat.use_nodes:
                            for old_parent_node in mat.node_tree.nodes:                         # for loop B
                                #if old_parent_node.name.find("Cutaway Shader") != -1:
                                if "Cutaway Shader" in old_parent_node.name:
                                    if old_pynode_id == self.get_unique_pynode_id_str__create_if_neccessary(old_parent_node):
                                        # we have found our (old) parent). make the old parent a child node
                                        old_parent_node.make_a_child_node(new_pynode_id)
                                        
                                        old_parent_node.this_childs_parent_pynode_unique_id_str = new_pynode_id
                                        
                                        # Set the OSL node to the inner mesh setting
                                        #oslNode = old_parent_node.id_data.nodes[old_parent_node.osl_nodename_str]
                                        #oslNode.inputs["InnerMesh0_OuterMesh1"].default_value = 0
                                        
                                        # add the new child node to our list of child nodes (since we are now the parent)
                                        self.append_child_unique_pynode_id_to_parents_master_child_dict(old_parent_node)
                                        
                                        # erase the old parents child list - as it no longer needs it.
                                        for child_key_str in old_parent_node.keys():            # for loop C
                                            # not all keys belong to the 'parent's node unique id' (pnuid) so check that pnuid is in the key name
                                            if child_key_str.find("pnuid") > -1:
                                                # extract the child node unique id str from the dict
                                                del old_parent_node[child_key_str]
                                                
                                        exit = True
                                        break                                                   # exit for loop B. no need to check more nodes in the tree
                                    
                                    # DSW::::   up to here: All children must be updated with their new parent. Add this to the large automated list thingy
                        if (exit):                                                              # exit for loop A. no need to check more materials in the file
                            break;
                                        

    def update(self):
        #print("updating", self)
        return
        
    def free(self):
        #print("Removing node ", self, ", Goodbye!")
        return
        
            
    # --------------------------------------------------------------------------------------------
    # --------------------------------------------------------------------------------------------
    # Draw all the GUI elements into the py node. Required by py node API
    # This is what the user sees in the node editor.
    def draw_buttons(self, context, layout):
        is_parent = self.node_is_parent
        
        # Debug display:
        # Display this nodes unique id
        id_str = "No I.D"
        if "unique_pynode_id_str" in self.keys():
            id_str = self["unique_pynode_id_str"]
        row = layout.row(align=True)                                  
        row.label("Node ID:" + id_str)  
        
        wmid_int= "no sc counter"
        #wm = bpy.data.window_managers[0]
        if "pynode_unique_id_counter_int" in bpy.context.scene.keys():
            wmid_int = bpy.context.scene['pynode_unique_id_counter_int'] 
        row = layout.row(align=True)                                  
        row.label("Counter:" + str(wmid_int)) 
        
        #global cut_away_shader_global_pynode_list
        #row = layout.row(align=True)                                  
        #row.label("Len " + str(len(cut_away_shader_global_pynode_list))) 
        
       
        #wmid_int2= "no wm2 counter"
        #wm = bpy.data.window_managers[0]
        #if "pynode_unique_id_counter_int2" in wm.keys():
        #    wmid_int2 = wm['pynode_unique_id_counter_int2'] 
        #row = layout.row(align=True)                                  
        #row.label("Counter2:" + str(wmid_int2)) 
       
            
        
        # Determine if OSL + CPU rendering is enabled
        osl_alert_bool = (bpy.context.scene.cycles.shading_system != True) or (bpy.context.scene.cycles.device  !='CPU')  
        if (osl_alert_bool):
            icon_str = "ERROR"
        else:
            icon_str = "NONE"
            
        layout.separator()
        layout.separator() 
          
        # Enable OSL and CPU Rendering Button   
        # Button only enabled if OSL not enabled and/or GPU mode selected  
        # An 'alert' icon is displayed if OSL + CPU needs enabling.                                         
        row = layout.row(align=True)
        row.enabled = osl_alert_bool                                       
        row.label("Enable OSL Rendering:", icon = icon_str)  
        row.operator("cas_btn.enable_osl",  # <=== Button code to execute when pressed (search for this)
                     "Enable CPU + OSL",    # <=== Text in the button
                     icon = 'NONE') 
        
        layout.separator()   
        layout.separator()   
        
        # Layout for Parent Nodes
        if (is_parent): 
            # Shader Output Mix Title   
            row = layout.row(align=True)                            
            row.label("Shader Output Mix:")                                                  
            
            # Cut away Effect Mix Slider
            row = layout.row(align=False)
            row.prop(self, "effectmix_float", "Cutaway Effect Mix", slider = True)          
            
            # Rim Fill Effect Mix Slider
            row = layout.row(align=True)
            row.enabled =  self.fillRim_bool_prop  and is_parent
            row.prop(self, "rimeffectmix_float", "Rim Fill Effect Mix", slider = True)    
 
            layout.separator()
            
            # Determine the name of the selected cutaway plane (if any)
            # An 'alert' icon is displayed of no plane is currently selected
            setup_node = self.id_data.nodes[self.py_nodename_str]
            cutawayplane_namestr = setup_node.cutAwayPlaneNameStr                           #<= bug here if plane deleted?
            icon_str = 'NONE' 
            enable_plane_options_bool = True                                                # icon = 'OUTLINER_OB_MESH'
            if (cutawayplane_namestr == ""):
                cutawayplane_namestr = "Select Cutaway Plane"
                icon_str = 'ERROR'
                enable_plane_options_bool = False
            
            # Cutaway Plane Settings Title
            row = layout.row(align=True)
            row.label("Cutaway Plane Settings:")              
            
            # Add Cutaway Plane Button
            row = layout.row(align=True)
            row.label("Add Cutaway Plane")                                                 
      
            row.operator(   "cas_btn.add_cutawayplane",                                # <=== Button code to execute when pressed (search for this)
                            "Add Cutaway Plane",                                       # <=== Text in the button
                             icon=icon_str).setupnode_namestr2 = self.py_nodename_str  # <=== Pass this py nodes name to the button execution code.
                                                                                       #      This name is used by the button code to reference this pynode.
                                                                                       #      This will allow the button to call code in this pynode
                                                                                       #      (Node button code (i.e. operator code) is not contained
                                                                                       #      within the pynode class - hence the need for the reference)
            #layout.separator()
            
            # Select Cutaway PlaneButton
            row = layout.row(align=True) 
            row.label("Select Cutaway Plane", icon = icon_str)                                                                                        
            row.operator(
                "cas_btn.select_cutaway_plane",                                        # <=== Button code to execute when pressed (search for this)
                text = cutawayplane_namestr,                                           # <=== Text in the button
                icon = icon_str).setupnode_namestr = self.py_nodename_str              # <=== Same as above ... 

            layout.separator()
            layout.separator()      
   
            # Cutaway Plane Origin: Center Button
            row = layout.row(align=True)
            row.enabled = enable_plane_options_bool
            row.label("Cutaway Plane Origin") 
            row.operator(   "cas_btn.origin_reset", 
                            "Center").setupnode_namestr4 = self.py_nodename_str  
            
            # Cutaway Plane Origin: Cursor Button
            row = layout.row(align=True)
            row.enabled = enable_plane_options_bool  
            row.label("")    
            row.label("")                                                                   
            row.operator(   "cas_btn.origin_to_cursor", 
                            "To Cursor").setupnode_namestr3 = self.py_nodename_str   
            # Cutaway Plane Origin: Edge Selector : Edge Counter
            row.prop(self,   "edgeIndex_int_prop","Edge")
            
            
            # Refresh Cutaway plane (after vertex edit)
            row = layout.row(align=True) 
            row.enabled = enable_plane_options_bool
            row.label("After Vertex Edit")                                                                                         
            row.operator( 
                "cas_btn.refresh_cutaway_plane", 
                text = "Refresh Vertices").setupnode_namestr_rcp = self.py_nodename_str    # <=== (Almost) all setupnode_namestr_xxx variables  use the following format. 
                                                                                               #      The initials of the callback routine are used as the namse_str_  suffix.
                                                                                               #      e.g. setupnode_namestr_rcp
                                                                                               #      Refresh_Cutaway_Plane initials = rcp
                                                                                               #      hence: setupnode_namestr_rcp
                                                                                               #      This is because the properties defined in the button operators (e.g. setupnode_namestr_rcp) 
                                                                                               #      cannot share the same name as any other operators properties. This suffix
                                                                                               #      scheme is an easy way of providing a 'unique' name.
                                                                                               
            layout.separator()
            layout.separator()
            
            # Cutaway Shape Rectangular/CircularCombo Box
            row = layout.row(align=True)
            row.enabled = enable_plane_options_bool  
            row.label("Cutaway Shape")                                                      
            row.prop(self, "draw_mode_enum", text="") 
            
            # Cutaway Image File
            #filenamestr = os.path.basename(self.cutaway_image_path_and_name_str)
            filenamestr = bpy.path.basename(self.cutaway_image_path_and_name_str)
            if (filenamestr== ""):
                filenamestr = "Open Image" 
                
            iconStr = "ERROR"
            #if (os.path.exists(os.path.abspath(self.cutaway_image_path_and_name_str))):
            if (os.path.exists(bpy.path.abspath(self.cutaway_image_path_and_name_str)) or self.rectangular_circular_int is not  2): # 2 = image based cutawway plane
                iconStr = "NONE"
                  
            row = layout.row(align=True)
            row.enabled = self.rectangular_circular_int == 2        # 2 = image based cutawway plane
            row.label("Cutaway Image File:")  
            row.label(filenamestr,icon = iconStr)       
            row.operator( 
                "cas_btn.open_image_dialog",  
                text = "",
                icon = "FILESEL").setupnode_namestr_iai = self.py_nodename_str 
            
            # Invert Cutaway Bounds Checkbox
            row = layout.row(align=True) 
            row.label("Cutaway Boundary")  
            row.prop(self, "invert_cutaway_bounds_prop", text = "Invert")  
            
            # Edge Fade Distance
            row = layout.row(align=True) 
            row.enabled = self.rectangular_circular_int != 2  
            row.label("Cutaway Edge Fade")  
            row.prop(self, "edge_fade_distance_float_prop", "Distance") #, slider = True) 
            
            # Edge Fade Sharpness
            row = layout.row(align=True) 
            row.enabled = self.rectangular_circular_int != 2  
            row.label("Cutaway Edge Sharpness")  
            row.prop(self, "edge_fade_sharpness_float_prop", "Sharpness", slider = True)
            
            layout.separator() 
            
            # Solidify/Rim Fill Options title
            row = layout.row(align=False) 
            row.enabled = self.rectangular_circular_int == 1 
            row.label("Solidify/Rim Fill Options:")
            
            # Solidify Active Object Button
            row = layout.row(align=False) 
            row.enabled = self.rectangular_circular_int == 1 
            row.label("Add Modifier") 
            row.operator(   
                "cas_btn.add_inner_solidifier_mesh_and_material",                                                                      
                "Solidify Active Object",
                icon = "MATERIAL").setupnode_namestr_aismam = self.py_nodename_str  
            
            # Enable Rim Fill Checkbox
            row = layout.row(align=False)
            row.enabled = self.rectangular_circular_int == 1  
            row.label("") 
            row.prop(self, "fillRim_bool_prop", "Enable Rim Fill")  
            
            enable_rim_fill_options_bool = self.fillRim_bool_prop and is_parent and self.rectangular_circular_int == 1 
            
             # Rim Occlusion Checkbox
            row = layout.row(align=False) 
            row.enabled = enable_rim_fill_options_bool 
            row.label("")  
            row.prop(self, "occludeRim_bool_prop")                                          
            
            # Rim Thickness Slider
            row = layout.row(align=False) 
            row.enabled =  enable_rim_fill_options_bool
            row.label("")  
            row.prop(self, "rimthickness_float", "Rim Thickness") #, slider = True)  
            
            layout.separator()
            

            #layout.separator()
            
            #has_childnodes = self.get_items_in_child_list_str() > 0;
            has_childnodes = True
            for keystr in self.keys():
                #print (keystr)
                if  keystr.find("puid") != -1:
                    has_childnodes = True
                    break
                    
           
            # Child Node Options  Title
            row = layout.row(align=False)                                                   
            row.enabled = is_parent
            #row.label("Child Objects of this Shader:") 
            row.label("Parenting:")
            
            # Add Child Nodes to Selected Objects Button
            row = layout.row(align=False)             
            row.enabled = is_parent 
            row.operator(   "cas_btn.add_child_nodes_to_selected", 
                            "Add Child Cutaway Shader to Selected Objs", 
                             icon = "MATERIAL").setupnode_namestr_asts = self.py_nodename_str 
                             
            # Remove Selected Children Button
            row = layout.row(align=False)                                                   
            row.enabled = is_parent and has_childnodes            
            row.operator(   "cas_btn.remove_child_nodes_from_selected", 
                            "Remove Child Shader from Selcted Objects", 
                             icon = "MATERIAL").setupnode_namestr_rsfs = self.py_nodename_str 
                             
            layout.separator()
              
            # Object Selection for this Shader  Title
            row = layout.row(align=False)                                                   
            row.enabled = is_parent
            row.label("Object Selection:") 
            
            # Select All Parent Objects Button                 
            row = layout.row(align=False)                                                   
            row.enabled = is_parent  # and has_childnodes 
            row.operator(   "cas_btn.select_all_objects_using_this_parent_node",        #select_all_parents", 
                            "Select Parent Objects", 
                             icon = "MATERIAL").setupnode_namestr_sap = self.py_nodename_str 
            
            # Select All Child Objects Button                 
            row = layout.row(align=False)                                                   
            row.enabled = is_parent and has_childnodes 
            row.operator(   "cas_btn.select_all_child_nodes",                           # select_all_child_nodes
                            "Select Child Objects", 
                             icon = "MATERIAL").setupnode_namestr_sas = self.py_nodename_str  
                                        
            # Select All Parent objects in the SceneButton                 
            row = layout.row(align=False)                                                   
            row.enabled = is_parent
            row.operator(   "cas_btn.select_all_parents_in_scene", 
                            "Select All Parent Objects in the Scene", 
                             icon = "MATERIAL").setupnode_namestr_sapis = self.py_nodename_str 
            
            layout.separator()
            
            # Refresh Cutaway plane (after frame change) 
            checked_bool = True;
            if 'global_auto_update_child_nodes_on_frame_change_bool' in bpy.context.scene.keys():
                checked_bool = bpy.context.scene['global_auto_update_child_nodes_on_frame_change_bool']
            if (checked_bool):
                tick_icon = 'CHECKBOX_HLT'
            else:
                tick_icon = 'CHECKBOX_DEHLT'
            row = layout.row(align=True)
            row.label("Child Nodes: 3D Preview: Refresh after frame change")  
            
            row = layout.row(align=True) 
            row.operator( 
                "cas_btn.auto_refresh_child_nodes_after_frame_change",icon = tick_icon,        # Auto Refresh After Key Frame Change
                text = "Auto Refresh").setupnode_namestr_arcnafc = self.py_nodename_str        # <=== (Almost) all setupnode_namestr_xxx variables  use the following format. 
                                                                                               #      The initials of the callback routine are used as the namse_str_  suffix.
                                                                                               #      e.g. setupnode_namestr_arcnafc
                                                                                               #      auto_refresh_child_nodes_after_frame_change initials = arcnafc
                                                                                               #      hence: setupnode_namestr_arcnafc
                                                                                               #      This is because the properties defined in the button operators (e.g. setupnode_namestr_arcnafc) 
                                                                                               #      cannot share the same name as any other operators properties. This suffix
                                                                                               #      scheme is an easy way of providing a 'unique' name.  
                                                                                               # To find all the code associated with this (or any other button/gui element), just search 
                                                                                               # on the name of the button: e.g. auto_refresh_child_nodes_after_frame_change in this case
                                                                                               # By convention, all code related to the gui properties use auto_refresh_child_nodes_after_frame_change''
                                                                                               # in the function definition names. This is true for (almost) all the properties below.
                                                                                         
            row.operator( 
                "cas_btn.manual_refresh_child_nodes_after_frame_change",                       # Manual Refresh After Key Frame Change 
                text = "Manual Refresh").setupnode_namestr_mrcnafc = self.py_nodename_str      # <=== (Almost) all setupnode_namestr_xxx variables  use the following format. 
                                                                                               #      The initials of the callback routine are used as the namse_str_  suffix.
                                                                                               #      e.g. setupnode_namestr_mrcnafc
                                                                                               #      setupnode_namestr_mrcnafc initials => mrcnafc
                                                                                               #      hence: setupnode_namestr_mrcnafc
                                                                                               #      This is because the properties defined in the button operators (e.g. setupnode_namestr_rcp) 
                                                                                               #      cannot share the same name as any other operators properties. This suffix
                                                                                               #      scheme is an easy way of providing a 'unique' name.  
                                                                                               
            layout.separator()                                                                                   
            
            # Delete All Cutaway Shader Nodes
            row = layout.row(align=False)                                                   
            row.enabled = is_parent
            row.alert = True
            row.label("Fast Delete") 
            
            # Remove All CutAway Shader Nodes                 
            row = layout.row(align=False)                                                   
            row.enabled = is_parent
            
            #row.operator(   "cas_btn.remove_all_cut_away_shader_nodes", 
            #                "Remove All CutAway Shader Nodes", 
            #                 icon = "MATERIAL").setupnode_namestr_racsn = self.py_nodename_str  
            row.operator(   "cas_btn.warning_dialog_operator", 
                            "Delete *ALL* CutAway Shader Nodes ...", 
                             icon = "MATERIAL").setupnode_namestr_wdo = self.py_nodename_str                     
                             
        
        # Layout for Child Nodes
        else:
            layout.separator()         
            layout.separator() 
            layout.separator() 
            
            if (self.orphaned_child_node_bool):
                row = layout.row(align=True)  
                row.label("This child node no longer has a parent.") 
                row = layout.row(align=True) 
                row.label("(The orginal parent object/material may have been")
                row = layout.row(align=True) 
                row.label("deleted)")
                layout.separator()
                row = layout.row(align=True) 
                row.label("Select 'Unlink' access this nodes settings.")
                layout.separator()
                layout.separator()
            else:
                # Create some space
                for i in range(0,8):
                    layout.separator()

            #row = layout.row(align=False)                                                           
            #row.enabled = True   
            
            # Parent Nodes Material Name info text
            #row = layout.row(align=True)  
            #row.label("Parent Material Name: " + self.parent_cshader_mat_idstr )             #pchng - addget
             
            # Parent Nodes Name info text
            #row = layout.row(align=False)   
            #row.label("Parent Node Name    : " + self.parent_node_name_str  )  
            
            #layout.separator()
                                              
            
            # Unlink Child from Paent Button
            row = layout.row(align=True)  
            row.label("Unlink This Child Node from Parent Node") 
            row = layout.row(align=True) 
            row.operator(                                        
                "cas_btn.unlink_child", "Unlink").setupnode_namestr2 = self.py_nodename_str  
            
            # Node Tree View: Title
            row = layout.row(align=False)                                                           
            row.label("Node Tree View:")  
            row = layout.row(align=False) 
            # Select Parent Object Button
            row.operator(                                                               # Select Parent Object button 
                "cas_btn.select_parent_node", 
                "Select Parent Object").setupnode_namestr_spo = self.py_nodename_str
            # Jump to Parent Node Button      
            row.operator(                                                               # Jump To child Node Tree View button 
                "cas_btn.jump_to_parent_node", 
                "Jump to Parent Node").setupnode_namestr90 = self.py_nodename_str  
            row = layout.row(align=False) 
            # Select all Objects using this Child Shader Node Button      
            row.operator(                                                               # Jump To child Node Tree View button 
                "cas_btn.select_all_objects_using_this_child_node", 
                "Select all Objects using this Child Shader").setupnode_namestr_saoutcs = self.py_nodename_str  



    # --------------------------------------------------------------------------------------------  
    # --------------------------------------------------------------------------------------------  
    # Optional pynode API methods
    
    # Optional pynode API method
    # Detail buttons in the sidebar. If this function is not defined, the draw_buttons function is used instead
    #def draw_buttons_ext(self, context, layout):
        #layout.prop(self, "fillRim_bool_prop")
        # # Remove All CutAway Shader Nodes                 
        # row = layout.row(align=False)                                                   
        # row.enabled = is_parent
        # row.operator(   "cas_btn.remove_all_cut_away_shader_nodes", 
                        # "Remove All CutAway Shader Nodes", 
                         # icon = "MATERIAL").setupnode_namestr_racsn = self.py_nodename_str         

    '''
    # Optional pynode API method
    # Free function to clean up on removal.
    def free(self):
        print("Removing node ", self, ", Goodbye!")
     
    ## Optional pynode API method
    def draw_color(self, context, node):
        return (1.0, 0.0, 0.0, 0.0)
    '''
    
# End of pynode class code   
# --------------------------------------------------------------------------------------------




# ********************************************************************************************
# Custom node category definition
# Create a Catergory with the new custom nodes. This allows us to restrict the custom nodes to 
# the approprate node trees, and to group the new custom nodes in the appropriate "ADD Node" menus       
import nodeitems_utils
from nodeitems_utils import NodeCategory, NodeItem

# ShaderEffectsNodeCategory: Our own base class with an appropriate poll function, so the categories 
# only show up in the ShaderNodeTree screeen (and not the compositior node screen etc)
class ShaderEffectsNodeCategory(NodeCategory):
    # Poll function. Must return true if the node tree the user is viewing is a 'ShaderNodeTree' 
    @classmethod                                                 # callback            
    def poll(cls, context):                                      # Important: 
        return context.space_data.tree_type == 'ShaderNodeTree'  # <= This makes the CutAwaySetupNode accessable in the Shader node menu 

# Define the node categories that will be added as CUSTOM_NODES
# In this case we are just adding the ShaderEffectsNodeCategory
node_categories = [ShaderEffectsNodeCategory(   "OTHERNODES",                                   # identifier
                                                "Shader Effects",                               # menu display label
                                                items=[NodeItem("CutAwayShaderNodeType",        # CutAwayShaderNodeType is the class defined above,
                                                       label ='Cutaway Shader')  ])]            #'Cutaway Shader' is the label shown in the menu. 
                                                 


# ********************************************************************************************
# Register and Unregister cut away shader (cas) buttons and node                                            
def register():  
    bpy.utils.register_class(casBtnEnableOSL)
    bpy.utils.register_class(casBtnAddCutawayPlane) 
    bpy.utils.register_class(cas_btn_refresh_cutaway_plane) 
    bpy.utils.register_class(cas_btn_auto_refresh_child_nodes_after_frame_change)
    bpy.utils.register_class(cas_btn_manual_refresh_child_nodes_after_frame_change)
    bpy.utils.register_class(casBtnOpenImageDialog) 
    bpy.utils.register_class(casBtnAddChildNodesToSelected)   
    bpy.utils.register_class(casBtnRemoveChildNodesFromSelected)
    bpy.utils.register_class(casBtnSelectAllChildNodes)
    bpy.utils.register_class(casBtnSelectAllParents)
    bpy.utils.register_class(casBtnSelectAllParentsInScene)
    bpy.utils.register_class(casBtnRemoveAllCutAwayShaderNodes)
    bpy.utils.register_class(casBtnAddInnerSolidifyMeshAndMaterial) 
    bpy.utils.register_class(CasDynamicallyPopulateMenuForSelectPlane) 
    bpy.utils.register_class(casBtnSelectCutawayPlane) 
    bpy.utils.register_class(casBtnSelectParentObj) 
    bpy.utils.register_class(casBtnJumpToparentNode) 
    bpy.utils.register_class(casBtnSelectAllObjectsUsingThisChildNode)
    bpy.utils.register_class(casBtnPlaneOriginToCursor)
    bpy.utils.register_class(casBtnPlaneOriginReset)
    bpy.utils.register_class(casBtnUnlinkchildNode)
    bpy.utils.register_class(casWarningDialogOperator)
    bpy.utils.register_class(CutAwaySetupNode)

    try:
        nodeitems_utils.register_node_categories("CUSTOM_NODES", node_categories)               # Allows us to re-run the script when developing, without causing a re-registering error
    except:
        pass
    
    print("CutAwayShader running")
    
def unregister():
    nodeitems_utils.unregister_node_categories("CUSTOM_NODES")
    bpy.utils.unregister_class(CutAwaySetupNode)
    bpy.utils.unregister_class(casWarningDialogOperator)
    bpy.utils.unregister_class(casBtnUnlinkchildNode)
    bpy.utils.unregister_class(casBtnPlaneOriginReset)
    bpy.utils.unregister_class(casBtnPlaneOriginToCursor)
    bpy.utils.unregister_class(casBtnSelectAllObjectsUsingThisChildNode) 
    bpy.utils.unregister_class(casBtnJumpToparentNode)  
    bpy.utils.unregister_class(casBtnSelectParentObj)  
    bpy.utils.unregister_class(casBtnSelectCutawayPlane) 
    bpy.utils.unregister_class(CasDynamicallyPopulateMenuForSelectPlane)
    bpy.utils.unregister_class(casBtnAddInnerSolidifyMeshAndMaterial)
    bpy.utils.unregister_class(casBtnRemoveAllCutAwayShaderNodes)
    bpy.utils.unregister_class(casBtnSelectAllParentsInScene) 
    bpy.utils.unregister_class(casBtnSelectAllParents)
    bpy.utils.unregister_class(casBtnSelectAllChildNodes)  
    bpy.utils.unregister_class(casBtnRemoveChildNodesFromSelected)
    bpy.utils.unregister_class(casBtnAddChildNodesToSelected)
    bpy.utils.unregister_class(casBtnOpenImageDialog) 
    bpy.utils.unregister_class(cas_btn_manual_refresh_child_nodes_after_frame_change)
    bpy.utils.unregister_class(cas_btn_auto_refresh_child_nodes_after_frame_change)
    bpy.utils.unregister_class(cas_btn_refresh_cutaway_plane)  
    bpy.utils.unregister_class(casBtnAddCutawayPlane)
    bpy.utils.unregister_class(casBtnEnableOSL)
    


# Register if the "Run Script" button is pressed
# This will re-instantiate/init any existing cutaway shader pynodes that are in the .blend file
if __name__ == "__main__":
    register()

# Register if the CutAwayShader module is run on loading the .blend file. 
# The Register box muxt be ticked (Text.use_module=True) to have the script run on loading
# The user Pref "Auto Execution" must be checked to allow scripts to run on loading.
# This will re-instantiate/init any existing cutaway shader pynodes that are in the .blend file    
if __name__ == "CutAwayShader":
    register()
 
#**************************************************************************************
# Dev helper scripts
#**************************************************************************************
#def unique_pynode_id_exists_check2(pynode):
#    # Check if the unique_pynode_id_int has been defined
#    if 'unique_pynode_id_str' not in pynode.keys():
#        # No it hasn't - so define it
#        pynode['unique_pynode_id_str'] = '0'
#        
#    # Check if the pynode_unique_id_counter has been defined
#    wm = bpy.data.window_managers[0]
#    if 'pynode_unique_id_counter_int' not in wm.keys():
#        # No it hasn't - so define it
#        wm['pynode_unique_id_counter_int'] = 0
#        
#def reset_wm_counters():
#    wm = bpy.data.window_managers[0]
#    wm['pynode_unique_id_counter_int'] = 0
#     
#def create_unique_pynode_id_int(pynode, force_assignment_bool = False):
#    # Check that the pynode_unique_id_counter and unique_pynode_id_str exist - create them if they don't
#    unique_pynode_id_exists_check2(pynode)
#    
#    # if needed, assign a unique id to this cut away shader pynode, and increase the unique counter
#    unique_id_str = pynode['unique_pynode_id_str']
#    if force_assignment_bool or unique_id_str == '0':
#        wm = bpy.data.window_managers[0]
#        unique_id_str = str(wm['pynode_unique_id_counter_int'])
#        pynode['unique_pynode_id_str'] = unique_id_str
#        wm['pynode_unique_id_counter_int'] += 1
#        print("new id assigned", pynode.name, pynode['unique_pynode_id_str'])
#    
#    # return the pynode unique id    
#    return unique_id_str
#        
#def assign_unique_ids(reset_wm_counter_bool, force_reassignment_bool):
#    #if reset_wm_counter_bool:
#    #    reset_wm_counters()    
#    i = 0
#    for mat in bpy.data.materials:
#        i += 1
#        if mat.use_nodes:
#            j = 1
#            for node in mat.node_tree.nodes:
#                if node.name.find("Cutaway Shader") != -1:
#                    create_unique_pynode_id_int(node, force_reassignment_bool)
#                    if int(node['unique_pynode_id_str']) < 46:
#                        print ('sum_DEL ',i, j, node.name, node['unique_pynode_id_str'])
#                        del node['unique_pynode_id_str']
#                    else:    
#                        print('summary ',i, j, node.name, node['unique_pynode_id_str'])
#                        j +=1
#                    #print('summary ',i, j, node.name, node['unique_pynode_id_str'])
#                    #j +=1
#    print ("total = ", i*j)
#    
#def print_unique_ids(): 
#    wm = bpy.data.window_managers[0]
#    i = 0
#    for mat in bpy.data.materials:
#        i += 1
#        if mat.use_nodes:
#            j = 1
#            for node in mat.node_tree.nodes:
#                if node.name.find("Cutaway Shader") != -1:
#                    if 'unique_pynode_id_str' in node.keys():
#                        print('print ',i, j, node.name, node['unique_pynode_id_str'], wm['pynode_unique_id_counter_int'], mat.name)
#                    else:
#                        print('print ',i, j, node.name, '---', wm['pynode_unique_id_counter_int'])
#    print ("total = ", i*j)
 
#reset_wm_counters()                 
#assign_unique_ids(False, True)
#print_unique_ids();

# do do
# DONE:     Update Setup UI  
# DONE:     Shift UI elements to sockets for later node use
# DONE:     Link in currently selected cutaway shader                                                  
#           add in un register for menu dynamic menu
# DONE:     update OSL shader to deal with circles 
# DONE:     add ability to add cutaway planes (with pre-defined shading)
# DONE:     connect in in/outs to change effect mix 
# DONE:     update OSL shader to draw rims normal to the surface
# DONE:     make rim fill obey correct edges.
#           make fill work for circular. Need to change the "if ((fx < fillWidth*f2))" line(s)
# LEAVE     need extra 'FAC' feed through for local shaders. Need Global Fac(displacement) feed through.
# DONE      need to be able to choose Rim color / shader.
# LEAVE     add in plane texture lookup to OSL shader to allow arb shapes
# DONE      use bounding box - so planes can have their origin moved (then can get rid of edge centered mode)
# DONE      add in Rim effect mix
#           Test output factors
# DONE      Remove rim shader input
# DONE      Add auto links to inner mesh node.
#           Add labels to cutaway shader scripts
# DONE      Disable not used menus.
# DONE      Add jump to child node
# DONE      Add jump to parent node
# LEAVE     Red Color if no plane selected
#           make tutorials
#           update code to pep standard
# DONE      Need to init rim thickness
# DONE:     try multiple nodes <== look at how to get multiple planes into one material
# LEAVE     add camera visible toggle for the cutaway plane
# LEAVE     when user selects on Node - make the selected plane highlighted
# DONE      Get rid of parent / child node select. Just have link
# DONE      Print status in the child shader
# LEAVE?   * Reverse plane check box?
# DONE      Auto setting of child property when linking
#           copy scripts from addon into text editor
#           tidy code.
#           UNDO for ops.
# DONE      Need to update all nodes that use the plane with the altered origin.
# DONE      Support SELECT NONE to de-select child nodes.
#           OSL extra rim angle check
# DONE      Crash bug. Don't copy plane to child if no plane selected.
# DONE      Crash bug. Don't list self in child selection options
# DONE      Auto Create child Shader Material
# DONE      Fix edge to 3D cursor mode
# DONE      Fix placement of nodes when first created.
# DONE      Get rid of Version number input (hard wire for now)
#           Get rid of OSL B version number
#           Add addon v2.7+ check
# DONE      Add child list -- so parent can have multiple ChildNodes
#           Look at centering jump to view again - could save info when press jump to button.
# DONE      child's auto detach if their parent has gone -- leave as is - drivers are in place - user can un-link
#           Finalise how the addon copies the OSL text into the text area
# DONE      Fix crash when starting add plane ops from edit mode instead of object mode
#           Test all ops when starting in edit mode for crash
# DONE      Leave original material selected when selecting or editing the a new cut away plane.
# DONE      Add an operator to insert a ChildNodes into all the material slots of all the selected objects
# DONE      Add an operator to remove a parent shader from all selected 
# DONE      Add hints to the buttons
# DONE      Don't add solidifier if it already exists
# DONE      DOn't add new child mat if already exits
# DONE      Link in existing child mat to new object if it doesn't have one
# DONE      Select child linking bugs.
# LEAVE     Listen for socket connections / disconnections. Add/remove drivers
# DONE      Add OSL check box alert
# DONE      GET OSL default button state right
# DONE      Disable all SHADER if OSL not set
# DONE      Next step use child list
# DONE      allow ChildNodes to have individual materials when copying
# DONE      Add refresh plane after editing vertices (or auto refresh) --
# DONE      cant jump to parent after using add ChildNodes button
# DONE      Add auto parent settings copy after adding new ChildNodes
# DONE      Fix bug if matslot has no materials when adding, selecting or unlinking ChildNodes
# DONE      Fix bug when the selected cutaway plane is deleted. Done (ish)
# inprog    Fix bug when the selected cutaway plane is deleted - and then another plane is selected
# DONE      Restore the selection if a new cut away plane is selected.
# DONE      When using edge selection - reselect original object
#           When adding a plane -- compensate if the plane is does not have an origin at the center
# DONE      Clean the child list of objects that don't exist - 
# DONE      Add material when newly selected ChildNodes have none
# ---       Add ability to bypass selected ChildNodes / and/or parent child
# DONE      Add links to Rim Seg input.
#
#
# Done      Swap add CutAway Plane and Select Cutaway plane buttons
# Done      Fix select all layers bug (e.g. when select solidify obj)
# Done      Change M/S to Parent/Child nodes
# Done      Change M/S to Parent/Child nodes - user interface
#           Look at programing Add Cut Away Shader controls to Tabs  
# Done      Rim Fill not enabled by default for new Shader Nodes.   
# Done      Swap order of Solidify Button
# Done      Jump to parent node not working (for rim child)
# Done      Investigate if py shaders need unique names
#           Add a global mute
# Done      Fix bug if trying to add node to camera (etc)
# leave     Should we be able to make existing nodes child nodes via the parent?
# No        Should we be able to link existing nodes to Parent nodes 
# Done      If a child un links itself - it should remove its name from the child list
# Done      When add child node - restore the selection (don't select the cutaway plane)
# Done      Why is it so slow to set the mix factor when there is a child node.
# Done      Rim fill seems to be default enabled before check box is set
# Done      When selecting children - de-select all other objs first
# Done      Amalgamate the child node, material iteration code.
# Done      What about adding child nodes to objs with no material at all?
#           When switching from rect to circle cutaway with non center 
# Done      When going to circular - disable RimFill -- or write osl rim fill
# Done      Write OSL texture cutaway function.
# Done      When removing child nodes - do we also change the material name  (NO)-  as this is preventing us from adding child nodes again to this material slot. (not perhaps use properties).
# Done      Crashes when adding child nodes to .blend files with many materials (Note: was crashing when either no mat slot, or mat slot with no material)
# Done      create new child material in 0th slot (above BI materials)
# LEAVE     Simple convert of Blender Internal Materials (just duplicate diffuse & possibly transparency & ... texture ....)
# Done      When adding a dummy material to an empty slot (e.g. for a child material -- just make this the same child material -- the user can re-assign later). For thickness - make a unique material.
# Done      Easy linking of a material to a parent material?
# Done      When removing nodes - don't keep moving the diffuse material back.
#           Do we still need an update all child nodes?
# Done      Add in faster circular/rect switching
# Done      Disable rim fill when circular enabled.
# Done      Need a refresh button (for after cutaway plane edge edits)
# Done      After edge edits -- need to re-center the cutaway plane (end then restore edge mode? e.g. cursor mode etc).
# Leave     Perhaps need to count edges after a refresh - to decide whether to update all the goodies (or just take out some of the recent checks) 
# Done      If unlinking the default child - then make a duplicate. -*** still testing***
#           Select all orphaned child nodes.
#           Remove all cutaway shaders from selected.
# Done      Look at using material - object props instead of object names / material names.
# Done      Add unique cutaway shader property to object type - so that we don't have to rely on the user not re-naming objects. (obsolete)
# Done      Add unique cutaway shader property to material type so that we don't have to rely on the user not re-naming materials. line (obsolete)
#               1406 look for matslot.material.name == mat_name_str)  add prop to material. when refreshing - can search for child objs mat name from unique name list
# Done      When un-linking an object - check that the unique name is removed from the child list of the parent 
# Done      When choosing circular - must also disable the rim fill for the OSL shader (not just the py node)
# Done      Why is adding a solidify modifier not updating the name of the cutaway plane to its child node? Needs the unique obj name added to the list str.
# Done      find #pchng and change all instances of the parent material name to our material id, then change (all instances) of the name of the original name variable (obsolete)
#           Check why we are always creating a new material when making lots of material-less objs child objs.
# Done      Need duplicate material button? (NO)
# Done      Need to intercept object duplication. seet Text.001 for how to intercept scene change event. (obsolete)
# Done      need to create a duplicate last name. If new name not == last name then need to check if (obsolete)
# Done      we have duplicate obj_id_str in the scene. If so -- we up date our new obj_id_str (obsolete)
# ----      Could also use this callback to detect changes in vertex no.s if needed. (slow?) 
#                  or batfinger code: http://blenderartists.org/forum/showthread.php?328009-Unique-object-id&p=2585318&highlight=#post2585318 (obsolete)
# Done            The summary: We can assign a 'unique' number to objects. - but we can't detect when the object has its name changed.
# Done                       We can detect when an object is duplicated (this is what we want)
# Done                       We can create a list of assigned unique id's and store it (in the scene) say -- or maybe the WM
# Done                       The algorithm:     - Assign the unique id to the obj
# Done                                          - Store that unique id in the master list
# Done                                          - When we get a callback (on duplication) 
# Done                                                  - we need to allocate a new unique if (must append the new num
# Done                                                   - we need to search for our parent and insert ourselves in their child list                                              
# Done      Handle the duplication of many objects (some with child / parent cutaway shaders, some without.
# Done      More checking on duplication (ALT or SHIFT)
# Done      check wm keys  
# Done      Select Parent Node  
# Done      Fix add solidify bugs. a) not correctly setting up child node if no 2nd material (not copying parent settings to child). b) adding a child material to the main material if there is a second mat slot that exists.                                
# Done      -- Maybe we need to add ourselves to the child list when solidify modifying
# Done      Add controls to select image based cut away
# Done      Ensure that OSL occludes the rim when using a image based cutaway
# Done      Don't want to be able to add a child object to the parent.
# Done      Add filters to only show image for open dialog
#           If the object is a curve (and maybe some other types too) can't count vertices with BMESH for origin calculations (see crash line 2956)
# Done     If we add other shaders after the socket -- then we can't identify our cut away shader (should be looking for a matching name)
#           BUG: error if go to add child shader - when there is no shader connected to child material output.
# Done      Have to copy invert settings to the child nodes
# Done      Have to add the fall off distance and sharpness and then copy these to child nodes.
#           Copy invert settings when first created etc
# Done      Re-link orphaned node.
#           Make sure cutaway obj layer is selected when going into edit mode
#           (what about when layers are not all synced in 3D view)

#           When adding adding child nodes - if material exists - but does not use nodes (and is a cycles node) - then make it use nodes and then add a shader
#
# DONE      When adding a child shader - always duplicate the previous node (and set the prev # to fake? - not yet done)
# DONE      Only show image alert icon if the image mode is selected.
#
# DONE      Why does child link break if rename material node by hand? fixed
# DONE      Need to do a node select / deselect after a material unlink -- or add child nodes
# DONE      From 3306 - just added code to stop crash when cut away plane not on selected layer
# DONE      Fix jumping out og Node mode when changing Edge slider
# DONE      Fix Edit mode crash if selecting edge while local view when cutaway plane layer not enabled
# DONE      Fix Center operation when layers not selected.
# DONE      Enable hidden layers when user wants to show all objects using parent/child nodes.
#           Enable cutaway plane layer if hidden when the user selects it from the drop down menu.
#           Do orphan checks. (have added repair for get parent). Need to cycle though all mats and all child nodes and do this.
#           Context bug after deleting some cubes with child nodes from node editor.
#           When selecting all (or possibly other functions) we cannot go into object mode if no object is selected/active at all. All a select any obj if this is the case.
# RuntimeError: Operator bpy.ops.object.mode_set.poll() failed, context is incorrect
# I think this bug was because there was an object selected that could go into into edit mode (e.g. a lamp or an empty). maybe check if there is a mesh type object selected before doing the object context sensitive switch.
# DONE:     Find the pynode given the unique id
# DONE:     Find object(s) that use this pynode (given its unique id)
# DONE      Select the child nodes of a parent node (using the pynode unique ids)
# DONE      Add the unique id to the child lists of parents
# DONE      Add the unique id to the parent prop of child nodes
# DONE      Detect a duplicated node (and create a new id for the node), -- use copy node? If the duplicated is a parent -- then it needs to be made into a 'child of itself'.
# DONE      Detect a copied material (and create new ids for the shaders in the node tree. (could use the copy node as in above)
#           Duplicated 'child' objects will not need special precautions using this method.
#           Duplicated 'parent' objects will not need any special precautions.
#           check that the proper child / parent node props are updated when adding removing
# DONE      delete old list code.
# DONE      Check which pre/postframe callbacks get removed from filters.
# DONE      Add auto update child nodes on frame change option
#           Append cas_ to scene 'globals'. (to do)