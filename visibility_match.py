bl_info = {
    "name" : "zukii ni add-on",
    "author" : "kurol0", 
    "description" : "zukii ni no add-on",
    "blender" : (4,2,0),
    "version" : (1,0,0),
    "location" : "",
    "warning" : "",
    "doc_url": "", 
    "tracker_url": "https://chatgpt.com/", 
    "category" : "3D View" 
    }

import bpy
import os
from bpy.props import (BoolProperty, EnumProperty, PointerProperty)

target_items = [
    ("SELECT", "選択可能", "選択を無効 - 値の対象"),
    ("VIEWPORT_TEMP", "ビューポート : ViewLayer", "ビューポートで隠す - 値の対象"),
    ("VIEWPORT_GLOBAL", "ビューポート : Scene", "ビューポートで無効 - 値の対象"),
    ("RENDER", "レンダー", "レンダーで無効 - 値の対象"),
    ("HOLDOUT", "ホールドアウト", "ホールドアウト - 値の対象"),
#    ("NONE", "無し : テスト用", "Sync with test")
]

reference_items = [
    ("SELECT", "選択可能", "選択を無効 - 参照する値"),
    ("VIEWPORT_TEMP", "ビューポート : ViewLayer", "ビューポートで隠す - 参照する値"),
    ("VIEWPORT_GLOBAL", "ビューポート : Scene", "ビューポートで無効 - 参照する値"),
    ("RENDER", "レンダー", "レンダーで無効 - 参照する値"),
    ("HOLDOUT", "ホールドアウト", "ホールドアウト - 参照する値"),
    ("TRUE", "All True", "表示 - 値の無効(False)"),
    ("FALSE", "All False", "非表示 - 値の無効(True)"),
]

state_icon_map = {
    "SELECT": "RESTRICT_SELECT_OFF",
    "VIEWPORT_TEMP": "HIDE_OFF",
    "VIEWPORT_GLOBAL": "RESTRICT_VIEW_OFF",
    "RENDER": "RESTRICT_RENDER_OFF",
    "HOLDOUT": "HOLDOUT_ON",
    "TRUE": "ADD",
    "FALSE": "REMOVE",
    "NONE": "ERROR"
}

apply_exclude_map = {"ACTIVE", "SELECT", "VIEWPORT_GLOBAL", "RENDER", "TRUE", "FALSE"}  

# 保存イベントにフック
def pre_save_handler(dummy):
    preferences = bpy.context.preferences.addons[__name__.split(".")[0]].preferences
    cm_props = bpy.context.window_manager.cm_props
    
    # カスタムプロパティの削除
    if "reference" in cm_props:
        del cm_props["reference"]
    if "target" in cm_props:
        del cm_props["target"]

# ファイルをロードした後にデフォルト値を設定するハンドラ
def post_load_handler(dummy):
    preferences = bpy.context.preferences.addons[__name__.split(".")[0]].preferences
    cm_props = bpy.context.window_manager.cm_props

    # デフォルト値の再設定
    cm_props.reference = preferences.default_reference
    cm_props.target = preferences.default_target

# アドオンリファレンス
class VIEW3D_PT_preferences(bpy.types.AddonPreferences):
    bl_idname = __name__.split(".")[0]  # アドオン名が自動的に設定される
    
    default_reference: bpy.props.EnumProperty(
        name="Default Reference Mode",
        description="Choose which default reference mode to synchronize",
        items=reference_items,
        default="RENDER"
    )

    default_target: bpy.props.EnumProperty(
        name="Default Target Mode", 
        description="Choose which default target mode to synchronize",
        items=target_items,
        default="VIEWPORT_TEMP"
    )

#    reference: bpy.props.EnumProperty(
#        name="Reference Mode",
#        description="Choose which reference mode to synchronize",
#        items=reference_items
#    )

#    target: bpy.props.EnumProperty(
#        name="Target Mode",
#        description="Choose which target mode to synchronize",
#        items=target_items
#    )

    def draw(self, context):
        layout = self.layout
        
        # Default Reference
        row = layout.row()                        
        row.prop(self, "default_reference", text="Default Reference Mode")
        
        # Default Target
        row = layout.row()
        row.prop(self, "default_target", text="Default Target Mode")
     
class VIEW3D_PT_panel(bpy.types.Panel):
    bl_label = "Visibility"
    bl_idname = "VIEW3D_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "View"

    def draw(self, context):
        cm_props = context.window_manager.cm_props
        ref_state_icon = state_icon_map.get(cm_props.reference, "")
        tgt_state_icon = state_icon_map.get(cm_props.target, "")
        split_value = 0.2
        
        layout = self.layout
        layout.use_property_decorate = False  # アニメーション用の装飾を無効にする
        
        # 状態の一致を実行するボタン
        col = layout.column(align=True)
        row = col.row(align=True)
        row.operator("view3d.swap_states", text="",icon="UV_SYNC_SELECT")
        row.operator("view3d.condition_match", text="可視性の一致")
        
        row = layout.row()  
        row.prop(cm_props, "pattern", expand=True)
        
        # reference state
        row = layout.row()
        sub = row.split(factor=split_value)
        sub.alignment = "RIGHT"
        sub.label(text="参照:")
        col = sub.column(align=True)
        row = col.row(align=True)
        row.label(icon=ref_state_icon)
        row.prop(cm_props, "reference", text="")
      
        # target state
        row = layout.row()
        sub = row.split(factor=split_value)
        sub.alignment = "RIGHT"
        sub.label(text="対象:")
        col = sub.column(align=True)
        row = col.row(align=True) 
        row.label(icon=tgt_state_icon)
        row.prop(cm_props, "target", text="")
        
        # collection select
        row = layout.row()
        split = row.split(factor=split_value)
        split.alignment = "RIGHT"
        split.label(text="制限:") 
        split.prop_search(cm_props, "target_collection", bpy.data, "collections", text="")

class VIEW3D_PT_details_panel(bpy.types.Panel):
    bl_label = "オプション"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "View"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "VIEW3D_PT_panel"
    
    def draw(self, context):
        cm_props = context.window_manager.cm_props
        ref_state_icon = state_icon_map.get(cm_props.reference, "")
        tgt_state_icon = state_icon_map.get(cm_props.target, "")
        split_value = 0.2
        layout = self.layout
        layout.use_property_decorate = False
        
        # flip state value
        row = layout.row()
        row.use_property_split = True
        split = row.split(factor=split_value) 
        split.prop(cm_props, "flip_state_value", text="")
        split.label(text=" 値の反転")        

        # Without child collections
        row = layout.row()
        row.use_property_split = True
        sub = row.split(factor=split_value) 
        sub.prop(cm_props, "only_selected_objects", text="",emboss=True)
        sub.label(text=" 選択したオブジェクトのみ")
        
        # Without child collections
        row = layout.row()
        row.use_property_split = True
        sub = row.split(factor=split_value) 
        sub.active = cm_props.target_collection != None
        sub.prop(cm_props, "without_children", text="",emboss=True)
        sub.label(text=" 子コレクションを除外")
        
        # Apply exclude
        row = layout.row()
        row.use_property_split = True
        split = row.split(factor=split_value) 
        split.active = cm_props.target in apply_exclude_map and cm_props.reference in apply_exclude_map
        split.prop(cm_props, "apply_excludes_from_view_layer", text="")
        split.label(text=" ビューレイヤーから除外を使用")
           
class VIEW3D_OT_swap_states(bpy.types.Operator):
    """参照と対象を交換する"""
    bl_idname = "view3d.swap_states"
    bl_label = "Swap States"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        preferences = bpy.context.preferences.addons[__name__.split(".")[0]].preferences
        cm_props = context.window_manager.cm_props
        ref_state = cm_props.reference
        tgt_state = cm_props.target
        def_ref = preferences.default_reference
        def_tgt = preferences.default_target

        # swap refernce state and target state
        cm_props.reference = tgt_state if tgt_state in [item[0] for item in reference_items] else def_ref
        cm_props.target = ref_state if ref_state in [item[0] for item in target_items] else def_tgt
        
        return {"FINISHED"}

# 条件を一致させるオペレーター
class VIEW3D_OT_condition_match(bpy.types.Operator):
    """状態の一致"""
    bl_idname = "view3d.condition_match"
    bl_label = "Condition Match"
    bl_options = {"REGISTER", "UNDO"}
    
    def __init__(self):
        self.cm = None
    
    def execute(self, context):
        cm_props = context.window_manager.cm_props
        
        # CMの引数
        ref_state = cm_props.reference
        tgt_state = cm_props.target
        pattern = cm_props.pattern
        tgt_coll = cm_props.target_collection
        contain = not cm_props.without_children
        apply_excludes = cm_props.apply_excludes_from_view_layer
        flip_state_value = cm_props.flip_state_value
        
        self.cm = CM(
        ref_state, tgt_state, pattern, apply_excludes_from_view_layer=apply_excludes ,
         contain_child_collections=contain, target_collection=tgt_coll, flip_state_value=flip_state_value
        )
        error_message = self.cm.get_error
        # エラーメッセージのチェック
        if error_message:
            self.report({"ERROR"}, error_message)
            return {"CANCELLED"}
        else:
            self.cm.state
        
        return {"FINISHED"}
                
class CM:
    """
    指定されたパターンでコレクションまたはオブジェクトの状態を変更するメソッド

    Args:
        pattern: "obj_cm" (オブジェクトのみ), "coll_cm" (コレクションのみ), "coll_obj_cm" (両方)
        ref_state: 参照する状態 {"SELECT", "VIEWPORT_GLOBAL", "RENDER", "VIEWPORT_TEMP", "HOLDOUT", "ACTIVE", "TRUE", "FALSE"}
        tgt_state: 変更する状態 {"SELECT", "VIEWPORT_GLOBAL", "RENDER", "VIEWPORT_TEMP", "HOLDOUT"}
    """
    
    scene_state_map = {"SELECT", "VIEWPORT_GLOBAL", "RENDER"}
    view_layer_state_map = {"VIEWPORT_TEMP", "HOLDOUT"}
    other_state_map = {"TRUE", "FALSE", "ACTIVE"}
    pattern_map = {"obj_cm", "coll_cm", "coll_obj_cm"}
    error_message = ""

    def __init__(self, ref_state, tgt_state, pattern, *,apply_excludes_from_view_layer = False, contain_child_collections = False, target_collection = None, flip_state_value = False):
        self.ref_state = ref_state
        self.tgt_state = tgt_state
        self.pattern = pattern
        self.apply_excludes_from_view_layer = apply_excludes_from_view_layer
        self.contain_child_collections = contain_child_collections
        self.target_collection = target_collection
        self.flip_state_value = flip_state_value
        self.ref_type = None
        self.tgt_type = None 

    @property
    def ref_state(self):
        return self.__ref_state

    @ref_state.setter
    def ref_state(self, value):
        if value in CM.scene_state_map:
            self.__ref_type = "Scene"
        elif value in CM.view_layer_state_map:
            self.__ref_type = "ViewLayer"
        elif value in CM.other_state_map:
            self.__ref_type = "OTHER"
        else:
            self.error_message = ("ValueError: The string that can be used in tgt_state is: {} {} {}.".format(
                ', '.join(f"'{item}'" for item in CM.scene_state_map),
                ', '.join(f"'{item}'" for item in CM.view_layer_state_map),
                ', '.join(f"'{item}'" for item in CM.other_state_map)))
        self.__ref_state = value

    @property
    def tgt_state(self):
        return self.__tgt_state

    @tgt_state.setter
    def tgt_state(self, value):
        if value in CM.scene_state_map:
            self.__tgt_type = "Scene"
        elif value in CM.view_layer_state_map:
            self.__tgt_type = "ViewLayer"
        else:
            self.error_message = ("ValueError: The string that can be used in tgt_state is: {} {} .".format(
                ', '.join(f"'{item}'" for item in CM.scene_state_map),
                ', '.join(f"'{item}'" for item in CM.view_layer_state_map)))
        self.__tgt_state = value
        
    @property
    def apply_excludes_from_view_layer(self):
       return self.__apply_excludes_from_view_layer

    @apply_excludes_from_view_layer.setter
    def apply_excludes_from_view_layer(self, value):
        if not isinstance(value, bool):
            self.error_message = ("ValueError: apply_excludes_from_view_layer must be a boolean value.")
        self.__apply_excludes_from_view_layer = value
                
    @property
    def contain_child_collections(self):
       return self.__contain_child_collections

    @contain_child_collections.setter
    def contain_child_collections(self, value):
        if not isinstance(value, bool):
            self.error_message = ("ValueError: contain_child_collections must be a boolean value.")
        self.__contain_child_collections = value
        
    @property
    def target_collection(self):
        return self.__target_collection

    @target_collection.setter
    def target_collection(self, value):
        if value is not None:
            if not (self.__ref_type in {"Scene", "OTHER"} and self.__tgt_type == "Scene" and not self.__apply_excludes_from_view_layer):
                __tgt_coll = self.get_child_coll(bpy.context.view_layer.layer_collection, target_coll=value)
                if __tgt_coll is None:
                    self.error_message = "ValueError: 選択されたコレクション「{}」はビューレイヤー「{}」にいないため実行できません!".format(value.name,bpy.context.view_layer.name)
#                    self.error_message = ("ValueError: The selected collection does not exist in the current ViewLayer.")  

                elif  __tgt_coll.exclude:
                    self.error_message = "ValueError: 選択されたコレクション「{}」はビューレイヤー「{}」から除外されているため実行できません!".format(value.name,bpy.context.view_layer.name)
#                    self.error_message = ("ValueError: The selected collection is excluded from the view layer.")           
            else:
                __tgt_coll = self.get_child_coll(bpy.context.scene.collection, target_coll=value)
                if __tgt_coll is None:
                    self.error_message = "ValueError: 選択されたコレクション「{}」はシーン「{}」にいないため実行できません!".format(value.name,bpy.context.scene.name)
#                    self.error_message = ("ValueError: The selected collection does not exist in the current Scene.")                
                    
        self.__target_collection = value  
        
    @property
    def pattern(self):
        return self.__pattern

    @pattern.setter
    def pattern(self, value):
        if value not in CM.pattern_map:
            self.error_message = "ValueError: The string that can be used in pattern is: {}.".format(', '.join(f"'{item}'" for item in CM.pattern_map))
        self.__pattern = value
        
    @property
    def flip_state_value(self):
       return self.__flip_state_value

    @flip_state_value.setter
    def flip_state_value(self, value):
        if not isinstance(value, bool):
            self.error_message = ("ValueError: flip_state_value must be a boolean value.")
        self.__flip_state_value = value
        
    @property    
    def get_error(self):
        return self.error_message
        
    def get_child_coll(self, collection, child_coll=None, *, search_exclude=None, target_coll=None, add_parent_collection=False):
        """
        self.get_child_coll(collection, child_coll, search_exclude=None)
        コレクションの子コレクションを再帰的に探索してリストに追加し、child_collのリストを返す。
        Parameters:
        - collection(Collection(ID) ,LayerCollection, (never None)) 探索の基となるコレクションまたはレイヤーコレクション。
        - child_coll(list, (optional)) 追加に使用されるリスト。デフォルトはNone。
        - search_exclude(str, (optional)) "collection" または "layer_collection" を指定することで、特定のタイプのコレクションをフィルタリングする。デフォルトは None 。
        - add_parent_collection(bool, (optional)) True でリストの最初に親コレクションを追加します。デフォルトは False 。
            
        self.get_child_coll(collection, target_coll=None)
        指定コレクションがコレクションの中に存在するのかを再帰的に探索
        ターゲットコレクションが見つかればそれを返し、見つからなければ `None` を返す。
        Parameters:
        - collection(Collection(ID) ,LayerCollection, (never None)) 探索の基となるコレクションまたはレイヤーコレクション。
        - target_coll(Collection(ID) ,LayerCollection, (never None)) 指定コレクション。            
                    
        """
        if isinstance(collection, bpy.types.LayerCollection):
            bpy_type = "layer_collection"
        elif isinstance(collection, bpy.types.Collection):
            bpy_type = "collection"
        else:
            bpy_type = "None"
        
        if bpy_type == "None":
            raise ValueError("Not the corresponding bpy.types")
        
        if child_coll is None:
            child_coll = []  # 初めて呼び出されたときのみ空のリストを作成
        
        # new_collection = get_child_coll(collection, target_coll=None)
        if target_coll:
            if bpy_type == "layer_collection" and collection.collection == target_coll:
                return collection
            elif bpy_type == "collection" and collection == target_coll:
                return collection
            for child in collection.children:
                found = self.get_child_coll(child, target_coll=target_coll)
                if found:
                    return found
            return None
        
        # new_colleciton = get_child_coll(collection, search_exclude = " 'collection' or 'layer_collection' ", add_parent_collection="False or True")
        elif search_exclude:
            if bpy_type == "layer_collection":
                if search_exclude not in {"collection", "layer_collection"}:
                    raise ValueError("Incorrect use of search_exclude")
                if not isinstance(add_parent_collection, bool):
                    raise ValueError("add_parent_collection must be a boolean value.")
                if add_parent_collection:
                    child_coll.insert(0,collection)
                    
                for child_layer_collection in collection.children:
                    if not child_layer_collection.exclude:
                        child_coll.append(
                            child_layer_collection if search_exclude == "layer_collection" else child_layer_collection.collection
                        )
                    self.get_child_coll(child_layer_collection, child_coll, search_exclude=search_exclude)
            elif bpy_type == "collection":
                raise ValueError("Collections of type bpy.types.Collection cannot use search_exclude")
                
        # new_colleciton = get_child_coll(collection, add_parent_collection="False or True")            
        else:
            if not isinstance(add_parent_collection, bool):
                raise ValueError("add_parent_collection must be a boolean value.")
            if add_parent_collection:
                child_coll.insert(0,collection)
                
            for child in collection.children:
                if bpy_type == "layer_collection":
                    child_coll.append(child.collection)
                elif bpy_type == "collection":
                    child_coll.append(child)
                self.get_child_coll(child, child_coll)

        return child_coll

    def select_collection(self):

        ref_state = self.ref_state
        tgt_state = self.tgt_state
        ref_type = self.__ref_type
        tgt_type = self.__tgt_type
        tgt_coll = self.target_collection
        apply_excludes_from_view_layer = self.apply_excludes_from_view_layer
        get_child_coll = self.get_child_coll
        
        def parturn_get_child_coll(tgt_coll=None, search_exclude_type=None):
            layer_coll = bpy.context.view_layer.layer_collection 
            
            if search_exclude_type not in {"collection" ,"layer_collection", None}:
                 raise ValueError("search_exclude_type is only 'collection', 'layer_collection' or None.")    
                 
            if tgt_coll:
                parent_of_layer_coll = get_child_coll(layer_coll, target_coll=tgt_coll)
                if search_exclude_type:
                    return get_child_coll(parent_of_layer_coll, search_exclude=search_exclude_type, add_parent_collection=True)
                else:
                    return get_child_coll(bpy.data.collections[tgt_coll.name], add_parent_collection=True)
            else:
                if search_exclude_type:
                    return get_child_coll(layer_coll, search_exclude=search_exclude_type)
                else:
                    return get_child_coll(bpy.context.scene.collection)
                
        # Scene-Scene, OTHER-Scene                                                    
        if ref_type in {"Scene", "OTHER"} and tgt_type == "Scene":
            search_exclude_type = "layer_collection" if apply_excludes_from_view_layer else None
        # Scene-ViewLayer, OTHER-ViewLayer, ViewLayer-Scene, ViewLayer-ViewLayer                     
        elif ref_type == "ViewLayer" and tgt_type in {"ViewLayer", "Scene"} or ref_type in {"Scene", "OTHER"} and tgt_type == "ViewLayer":
            search_exclude_type = "layer_collection"   
        else:
            raise ValueError("Invalid ref_state and tgt_state.")  
                  
        coll=parturn_get_child_coll(tgt_coll, search_exclude_type)
        return coll

    def process_object(self,data):
        """
        ref_state in {"SELECT", "VIEWPORT_GLOBAL", "RENDER", "VIEWPORT_TEMP", "HOLDOUT", "ACTIVE", "TRUE", "FALSE"}
        tgt_state in {"SELECT", "VIEWPORT_GLOBAL", "RENDER", "VIEWPORT_TEMP", "HOLDOUT"}
        scene_state_map = {"SELECT", "VIEWPORT_GLOBAL", "RENDER"}
        view_layer_state_map = {"VIEWPORT_TEMP", "HOLDOUT"}
        other_state_map = {"ACTIVE", "TRUE", "FALSE"}
        ref_type = "Scene" : ref_state in scene_state_map, ref_type = "ViewLayer" : ref_state in view_laye _state_map, 
        ref_type = "OTHER" : ref_state in other_state_map
        tgt_type = "Scene" : tgt_state in scene_state_map, ref_type = "ViewLayer" : tgt_state in view_laye _state_map
        
        process_object(data{object, layer_collecton, collection})
        dataの状態を変更する関数
        Parameters:
        - data(Collection(ID) ,LayerCollection, Object(ID), (never None))入力されたdataからref_stateから参照した値をtgt_stateを対象にして値を反映させる
        
        """
        ref_state = self.ref_state
        tgt_state = self.tgt_state
        ref_type = self.__ref_type
        tgt_type = self.__tgt_type
        flip_state_value = self.flip_state_value

        if isinstance(data, bpy.types.LayerCollection):
            bpy_type = "layer_collection"
            layer_coll_data = data
        elif isinstance(data, bpy.types.Collection):
            bpy_type = "collection"
        elif isinstance(data, bpy.types.Object):
            bpy_type = "object"
        else:
            bpy_type = "None"
            
        if bpy_type == "None":
            raise ValueError("Not the corresponding bpy.types")        

        if ref_state:
            if ref_type in {"Scene", "OTHER"} and (tgt_type == "ViewLayer" or tgt_type == "Scene") and bpy_type == "layer_collection":
                 data = data.collection
            new_value = None
            
            if ref_state:
                if ref_state == "SELECT":
                    new_value = data.hide_select
                elif ref_state == "VIEWPORT_GLOBAL":
                    new_value = data.hide_viewport   
                elif ref_state == "RENDER":
                    new_value = data.hide_render
                elif ref_state == "VIEWPORT_TEMP":
                    if bpy_type == "object":
                        new_value = data.hide_get()
                    elif bpy_type == "layer_collection":
                        new_value = data.hide_viewport       
                elif ref_state == "HOLDOUT":
                    if bpy_type == "object":
                        new_value = not data.is_holdout
                    elif bpy_type == "layer_collection":
                        new_value = not data.holdout
                elif ref_state == "TRUE":
                    new_value = False
                elif ref_state == "FALSE":
                    new_value = True
                else:
                    raise ValueError("Not the corresponding ref_state")
                 
                if tgt_state:
                    print(tgt_state)
                    if flip_state_value:
                        new_value = not new_value
                    if ref_type in {"Scene", "OTHER"} and tgt_type == "ViewLayer" and bpy_type == "layer_collection":
                        data = layer_coll_data
                    if ref_type == "ViewLayer" and tgt_type == "Scene" and bpy_type == "layer_collection":
                         data = data.collection
                                             
                    if tgt_state == "SELECT":
                        data.hide_select = new_value
                    elif tgt_state == "VIEWPORT_GLOBAL":
                        data.hide_viewport = new_value
                    elif tgt_state == "RENDER":
                        data.hide_render = new_value    
                    elif tgt_state == "VIEWPORT_TEMP":
                        if bpy_type == "object":
                            data.hide_set(new_value) 
                        elif bpy_type == "layer_collection":
                             data.hide_viewport = new_value
                    elif tgt_state == "HOLDOUT": 
                        if bpy_type == "object":
                            data.is_holdout = not new_value
                        elif bpy_type == "layer_collection":
                            data.holdout = not new_value
                        else:
                            raise ValueError("Not the corresponding tgt_state")
        else:
            raise ValueError("Not the corresponding bpy.types")

           
    @property
    def state(self): 
        #クラス引数
        ref_state = self.ref_state
        ref_type = self.__ref_type
        tgt_type = self.__tgt_type
        apply_excludes = self.apply_excludes_from_view_layer
        pattern = self.pattern
        target_collection = self.target_collection
        contain_child_collections = self.contain_child_collections
        coll = self.select_collection()
        layer_coll = bpy.context.view_layer.layer_collection
        
        #メソッド関数
        get_child_coll = self.get_child_coll
        process_object = self.process_object
        
        if ref_type == "ViewLayer" or ref_type in {"Scene", "OTHER"} and (tgt_type == "ViewLayer" or tgt_type == "Scene" and apply_excludes):   
             type = "lyaer_coll"
             
        elif ref_type in {"Scene", "OTHER"} and tgt_type == "Scene" and not apply_excludes:
            type = "scene_coll"
            
        else:
            raise ValueError("There is an anomaly in ref_type and tgt_type.")
            
        if ref_state == "ACTIVE":
            print("オブジェクト")
            for obj in bpy.context.selected_objects:
                process_object(obj)              
             
        elif pattern == "obj_cm":
            print("オブジェクト")     
            if target_collection and not contain_child_collections:
                if type == "lyaer_coll":
                    coll = get_child_coll(layer_coll, target_coll=target_collection)
                    if not coll.exclude:
                        for obj in coll.collection.objects:
                            process_object(obj)
                    else:
                        raise ValueError("None collection")
                else:
                    for obj in bpy.data.collections[target_collection.name].objects:
                        process_object(obj)  
            else:
                for collection in coll:                      
                    if type == "lyaer_coll":
                        for obj in collection.collection.objects:
                            process_object(obj)  
                    else: 
                        for obj in collection.objects:
                            process_object(obj)
                            
        elif pattern == "coll_cm":
            print("コレクション")
            if target_collection and not contain_child_collections:
                if type == "lyaer_coll":
                    coll = get_child_coll(layer_coll, target_coll=target_collection)
                    if not coll.exclude:
                        process_object(coll)
                    else:
                        raise ValueError("None collection")
                else:
                    process_object(bpy.data.collections[target_collection.name])
            else:
                for collection in coll:
                    process_object(collection)
                
        elif pattern == "coll_obj_cm":
            print("コレクションとオブジェクト")
            if target_collection and not contain_child_collections:
                if type == "lyaer_coll":
                    coll = get_child_coll(layer_coll, target_coll=target_collection)
                    if not coll.exclude:
                        process_object(coll)
                        for obj in coll.collection.objects:
                            process_object(obj)
                    else:
                        raise ValueError("None collection")
                else:
                    process_object(bpy.data.collections[target_collection.name])
                    for obj in bpy.data.collections[target_collection.name].objects:
                        process_object(obj)                      
            else:
                for collection in coll:
                    process_object(collection)
                    if type == "lyaer_coll":
                        for obj in collection.collection.objects:
                            process_object(obj)  
                    else: 
                        for obj in collection.objects:
                            process_object(obj)                         
        else:
                print("Error: Invalid pattern")  
         

#type=CM_Props
class CM_Props(bpy.types.PropertyGroup):
    
    reference: bpy.props.EnumProperty(
        name="Reference Mode",
        description="Choose which reference mode to synchronize",
        items=reference_items
    )

    target: bpy.props.EnumProperty(
        name="Target Mode",
        description="Choose which target mode to synchronize",
        items=target_items
    )
    
    pattern: bpy.props.EnumProperty(
        name="Pattern",
        description="Choose which target mode to synchronize",
        items=[
        ("obj_cm", "obj", "Sync with Viewport"),
        ("coll_cm", "coll", "Sync with Viewport"),
        ("coll_obj_cm", "both", "Both object and collection")
        ],
        default="coll_obj_cm"
    )
    
    flip_state_value: bpy.props.BoolProperty(
        name="Apply the inverted visibillity value",
        description="反転させた可視性の値を適用します",
        default=False,
    )    

    only_selected_objects: bpy.props.BoolProperty(
        name="Only selected objects",
        description="選択したオブジェクトのみに適用します",
        default=False,
    )
    
    without_children: bpy.props.BoolProperty(
        name="Does not contain child collections",
        description="対象が親コレクションのみで子コレクションは含みません",
        default=False,
    )

    apply_excludes_from_view_layer: bpy.props.BoolProperty(
        name="Apply excludes from ViewLayer",
        description="参照と対象が Scene typeでビューレイヤーから除外を適用できるようにします ",
        default=True,
    ) 
    
    target_collection: bpy.props.PointerProperty(
        name="Target Collection",
        type=bpy.types.Collection,
    )
    
preview_collections = {}           

def register():
    bpy.utils.register_class(VIEW3D_PT_preferences)
    bpy.utils.register_class(VIEW3D_PT_panel)
    bpy.utils.register_class(VIEW3D_PT_details_panel)
    bpy.utils.register_class(VIEW3D_OT_swap_states)
    bpy.utils.register_class(VIEW3D_OT_condition_match)
    bpy.utils.register_class(CM_Props)
    bpy.app.handlers.save_pre.append(pre_save_handler)
    bpy.app.handlers.load_post.append(post_load_handler)
    bpy.types.WindowManager.cm_props = PointerProperty(type=CM_Props)

def unregister():
    bpy.utils.unregister_class(VIEW3D_PT_preferences)
    bpy.utils.unregister_class(VIEW3D_PT_panel)
    bpy.utils.unregister_class(VIEW3D_PT_details_panel)
    bpy.utils.unregister_class(VIEW3D_OT_swap_states)
    bpy.utils.unregister_class(VIEW3D_OT_condition_match)
    bpy.utils.unregister_class(CM_Props)
    bpy.app.handlers.save_pre.remove(pre_save_handler)
    bpy.app.handlers.load_post.remove(post_load_handler)
    del bpy.types.WindowManager.fm_props
    

if __name__ == "__main__":
    register()
