from typing import List, Optional, Tuple, Type
from pathlib import Path
import re
import os
from datetime import datetime
from src.plugin_system import (
    BasePlugin, register_plugin, BaseAction, BaseCommand,
    ComponentInfo, ActionActivationType, ChatMode
)
from src.plugin_system.base.config_types import ConfigField
from src.plugin_system.apis import chat_api

# ===== Action组件 =====

class MHWJHAction(BaseAction):
    """集会码Action - 集会码相关动作"""

    # === 基本信息（必须填写）===
    action_name = "MHWJHAction"
    action_description = "处理怪物猎人集会码相关内容"

    
    # === 关键词激活 ===
    focus_activation_type = ActionActivationType.KEYWORD
    normal_activation_type = ActionActivationType.KEYWORD
    parallel_action = False
    activation_keywords = ["集会", "集会码"]

    # === 功能描述（必须填写）===
    action_parameters = {
        "MHW_jhm_action":"当前需要执行的集会码指令，必须。请注意选择当前需要执行的指令，填写的为冒号后面的英文，若有人只说“集会码”三个字，默认是查询集会码。登记集会码：REG，删除集会码：DEL，查询集会码：QUE",
        "REG_jhm":"需要登记的集会码，可选。注意！！集会码只能包含英文、除了逗号句号以外的标点符号和数字，包括问号(？), 等号(=), 感叹号(!), 不可以包含中文。示例: '=f7TXWY8PE2z'。",
        "DEL_jhm":"需要删除的集会码行数，可选。可以是多个数字，例如：“1,3”表示删除第一、三行，或是“ALL”代表全部集会码"
    }
    action_require = [
        "有人需要登记、删除、查询怪猎集会码时使用",
        "若有人只说“集会码”三个字，默认是查询集会码"
        ]
    associated_types = ["text"]

    async def execute(self) -> Tuple[bool, str]:
        """执行集会码相关操作"""
        try:
            action = self.action_data.get("MHW_jhm_action", "").upper()
            safe_group = self.chat_stream.group_info.group_name
            
            # 从配置获取数据
            data_dir = self.get_config("storage.data_dir", "data/mhw_jh")
            max_entries = self.get_config("storage.max_entries", 5)
            file_prefix = self.get_config("storage.file_prefix", "p_notepad")
            enable_duplicate_check = self.get_config("behavior.enable_duplicate_check", True)
            enable_timestamp = self.get_config("behavior.enable_timestamp", True)

            # 确保数据目录存在（可能需要优化？）
            DATA_DIR = Path(data_dir)
            os.makedirs(DATA_DIR, exist_ok=True)
            note_file = DATA_DIR / f"{file_prefix}_{safe_group}.txt"
            
            # 处理不同指令
            if action == "REG":
                return await self._register_jhm(safe_group, note_file, max_entries, enable_duplicate_check, enable_timestamp)
            elif action == "QUE":
                return await self._query_jhm(safe_group, note_file)
            elif action == "DEL":
                return await self._delete_jhm(safe_group, note_file)
            else:
                await self.send_text(f"【{safe_group}】未知的集会码指令喵~")
                return False, "未知指令"
        except Exception as e:
            error_msg = f"【{safe_group}】处理集会码时出错了喵：{str(e)}"
            await self.send_text(error_msg)
            return False, str(e)        
        
    async def _register_jhm(self, safe_group: str, note_file: Path, max_entries: int, enable_duplicate_check: bool, enable_timestamp: bool) -> Tuple[bool, str]:
        """登记集会码"""
        content = self.action_data.get("REG_jhm", "").strip()
        if not content:
            await self.send_text(f"【{safe_group}】喵内记不住空气啦~~")
            return False, "空集会码"
        
        # 读取现有记录
        existing_entries = []
        if note_file.exists():
            with open(note_file, "r", encoding="utf-8") as f:
                existing_entries = f.readlines()
        
        # 检查集会码是否已存在（忽略时间戳）
        if enable_duplicate_check:
            existing_codes = self._extract_codes(existing_entries, enable_timestamp)
            if content in existing_codes:
                # 找到该集会码的行号
                line_num = next((i+1 for i, code in enumerate(existing_codes) if code == content), -1)
                if line_num > 0:
                    await self.send_text(f"【{safe_group}】这个集会码已经在第{line_num}行登记过了喵~")
                else:
                    await self.send_text(f"【{safe_group}】这个集会码已经登记过了喵~")
                return False, "重复集会码"
        
        # 添加时间戳
        if enable_timestamp:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_entry = f"[{timestamp}] {content}\n"
        else:
            new_entry = f"{content}\n"

        # 维护最多max_entries条记录（保留最新(max_entries-1)条 + 新记录）
        if len(existing_entries) >= max_entries:
            existing_entries = existing_entries[-(max_entries-1):]  # 保留最后(max_entries-1)条
            
        # 添加新记录并写入
        updated_entries = existing_entries + [new_entry]
        
        with open(note_file, "w", encoding="utf-8") as f:
            f.writelines(updated_entries)
        
        await self.send_text(f"【{safe_group}】集会码登记了喵：{content}")
        return True, "登记成功"

    def _extract_codes(self, entries: List[str], enable_timestamp: bool) -> List[str]:
        """从带时间戳的条目中提取纯集会码"""
        codes = []
        for entry in entries:
            if enable_timestamp:
                # 格式: [时间戳] 集会码
                parts = entry.split("] ", 1)
                if len(parts) > 1:
                    # 去除可能的换行符
                    code = parts[1].strip()
                    if code:
                        codes.append(code)
            else:
                # 没有时间戳，直接使用内容
                code = entry.strip()
                if code:
                    codes.append(code)
        return codes

    async def _query_jhm(self, safe_group: str, note_file: Path) -> Tuple[bool, str]:
        """查询集会码"""
        if not note_file.exists():
            await self.send_text(f"【{safe_group}】集会码是空的喵~没人打猎嘛？")
            return True, "空集会码"
        
        with open(note_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        if not lines:
            await self.send_text(f"【{safe_group}】集会码是空的喵~没人打猎嘛？")
            return True, "空集会码"
        
        # 添加行号格式化输出
        numbered_lines = [f"{i+1}. {line.strip()}\n" for i, line in enumerate(lines)]
        content = "".join(numbered_lines)
        await self.send_text(f"【{safe_group}】集会码在这里喵：\n{content}")
        return True, "查询成功"
    
    async def _delete_jhm(self, safe_group: str, note_file: Path) -> Tuple[bool, str]:
        """删除集会码"""
        del_param = self.action_data.get("DEL_jhm", "").strip().upper()
        
        # 处理全部删除
        if del_param == "ALL":
            if note_file.exists():
                note_file.unlink()
            await self.send_text(f"【{safe_group}】喵内把集会码忘光光了喵~")
            return True, "全部删除成功"
        
        # 处理指定行删除
        try:
            line_numbers = [int(num.strip()) for num in del_param.split(",") if num.strip().isdigit()]
            if not line_numbers:
                raise ValueError("无效的行号")
        except:
            await self.send_text(f"【{safe_group}】出现了奇奇怪怪的错误喵~可以再尝试一次喵~")
            return False, "无效的行号格式"
        
        if not note_file.exists():
            await self.send_text(f"【{safe_group}】集会码是空的喵~没人打猎嘛？")
            return True, "空文件"
        
        with open(note_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        if not lines:
            await self.send_text(f"【{safe_group}】集会码是空的喵~没人打猎嘛？")
            return True, "空内容"
        
        # 验证行号范围并排序（从大到小删除避免索引变化）
        valid_lines = sorted([num for num in line_numbers if 1 <= num <= len(lines)], reverse=True)
        if not valid_lines:
            await self.send_text(f"【{safe_group}】无效的行号喵~ 当前共有{len(lines)}条集会码喵！")
            return False, "无效行号范围"
        
        # 删除指定行
        for num in valid_lines:
            del lines[num - 1]
        
        # 写入更新后的内容
        with open(note_file, "w", encoding="utf-8") as f:
            f.writelines(lines)
        
        # 准备响应内容
        remaining = len(lines)
        if remaining > 0:
            numbered_lines = [f"{i+1}. {line.strip()}\n" for i, line in enumerate(lines)]
            content = "".join(numbered_lines)
            response = f"【{safe_group}】成功删除了{len(valid_lines)}行集会码喵~剩余的集会码在这里喵：\n{content}"
        else:
            response = f"【{safe_group}】成功删除了{len(valid_lines)}行集会码喵~现在没有任何的集会码了喵~"
        
        await self.send_text(response)
        return True, "删除成功"    

# ===== Command组件 =====

class MHWJHRegisterCommand(BaseCommand):
    """集会码登记Command - 登记怪物猎人集会码"""
    
    command_name = "mhw_jh_register"
    command_description = "登记怪物猎人集会码"
    command_pattern = r"/a\s+(?P<REG_jhm>[^\s]+)"
    intercept_message = True  # 拦截消息处理

    async def execute(self) -> Tuple[bool, Optional[str], bool]:
        """执行集会码登记操作"""
        try:
            content = self.matched_groups.get("REG_jhm")
            safe_group = self.message.chat_stream.group_info.group_name
            
            if not content:
                await self.send_text(f"【{safe_group}】喵内记不住空气啦~~")
                return False, "空集会码", False
            
            # 从配置获取数据
            data_dir = self.get_config("storage.data_dir", "data/mhw_jh")
            max_entries = self.get_config("storage.max_entries", 5)
            file_prefix = self.get_config("storage.file_prefix", "p_notepad")
            enable_duplicate_check = self.get_config("behavior.enable_duplicate_check", True)
            enable_timestamp = self.get_config("behavior.enable_timestamp", True)

            # 确保数据目录存在
            DATA_DIR = Path(data_dir)
            os.makedirs(DATA_DIR, exist_ok=True)
            note_file = DATA_DIR / f"{file_prefix}_{safe_group}.txt"
            
            # 读取现有记录
            existing_entries = []
            if note_file.exists():
                with open(note_file, "r", encoding="utf-8") as f:
                    existing_entries = f.readlines()
            
            # 检查集会码是否已存在（忽略时间戳）
            if enable_duplicate_check:
                existing_codes = self._extract_codes(existing_entries, enable_timestamp)
                if content in existing_codes:
                    # 找到该集会码的行号
                    line_num = next((i+1 for i, code in enumerate(existing_codes) if code == content), -1)
                    if line_num > 0:
                        await self.send_text(f"【{safe_group}】这个集会码已经在第{line_num}行登记过了喵~")
                    else:
                        await self.send_text(f"【{safe_group}】这个集会码已经登记过了喵~")
                    return False, "重复集会码", False
            
            # 添加时间戳
            if enable_timestamp:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                new_entry = f"[{timestamp}] {content}\n"
            else:
                new_entry = f"{content}\n"

            # 维护最多max_entries条记录（保留最新(max_entries-1)条 + 新记录）
            if len(existing_entries) >= max_entries:
                existing_entries = existing_entries[-(max_entries-1):]  # 保留最后(max_entries-1)条
                
            # 添加新记录并写入
            updated_entries = existing_entries + [new_entry]
            
            with open(note_file, "w", encoding="utf-8") as f:
                f.writelines(updated_entries)
            
            await self.send_text(f"【{safe_group}】集会码登记了喵：{content}")
            return True, "登记成功", False
        except Exception as e:
            error_msg = f"【{safe_group}】处理集会码时出错了喵：{str(e)}"
            await self.send_text(error_msg)
            return False, str(e), False
    
    def _extract_codes(self, entries: List[str], enable_timestamp: bool) -> List[str]:
        """从带时间戳的条目中提取纯集会码"""
        codes = []
        for entry in entries:
            if enable_timestamp:
                # 格式: [时间戳] 集会码
                parts = entry.split("] ", 1)
                if len(parts) > 1:
                    # 去除可能的换行符
                    code = parts[1].strip()
                    if code:
                        codes.append(code)
            else:
                # 没有时间戳，直接使用内容
                code = entry.strip()
                if code:
                    codes.append(code)
        return codes


class MHWJHQueryCommand(BaseCommand):
    """集会码查询Command - 查询怪物猎人集会码"""
    
    command_name = "mhw_jh_query"
    command_description = "查询怪物猎人集会码"
    command_pattern = r"/p"
    intercept_message = True  # 拦截消息处理

    async def execute(self) -> Tuple[bool, Optional[str], bool]:
        """执行集会码查询操作"""
        try:
            safe_group = self.message.chat_stream.group_info.group_name
            
            # 从配置获取数据
            data_dir = self.get_config("storage.data_dir", "data/mhw_jh")
            file_prefix = self.get_config("storage.file_prefix", "p_notepad")

            # 确保数据目录存在
            DATA_DIR = Path(data_dir)
            note_file = DATA_DIR / f"{file_prefix}_{safe_group}.txt"
            
            if not note_file.exists():
                await self.send_text(f"【{safe_group}】集会码是空的喵~没人打猎嘛？")
                return True, "空集会码", False
            
            with open(note_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            if not lines:
                await self.send_text(f"【{safe_group}】集会码是空的喵~没人打猎嘛？")
                return True, "空集会码", False
            
            # 添加行号格式化输出
            numbered_lines = [f"{i+1}. {line.strip()}\n" for i, line in enumerate(lines)]
            content = "".join(numbered_lines)
            await self.send_text(f"【{safe_group}】集会码在这里喵：\n{content}")
            return True, "查询成功", False
        except Exception as e:
            error_msg = f"【{safe_group}】处理集会码时出错了喵：{str(e)}"
            await self.send_text(error_msg)
            return False, str(e), False


class MHWJHDeleteCommand(BaseCommand):
    """集会码删除Command - 删除怪物猎人集会码"""
    
    command_name = "mhw_jh_delete"
    command_description = "删除怪物猎人集会码"
    command_pattern = r"/d\s+(?P<DEL_jhm>.+)"
    intercept_message = True  # 拦截消息处理

    async def execute(self) -> Tuple[bool, Optional[str], bool]:
        """执行集会码删除操作"""
        try:
            del_param = self.matched_groups.get("DEL_jhm")
            safe_group = self.message.chat_stream.group_info.group_name
            
            # 从配置获取数据
            data_dir = self.get_config("storage.data_dir", "data/mhw_jh")
            file_prefix = self.get_config("storage.file_prefix", "p_notepad")

            # 确保数据目录存在
            DATA_DIR = Path(data_dir)
            note_file = DATA_DIR / f"{file_prefix}_{safe_group}.txt"
            
            # 处理全部删除
            if del_param == "ALL":
                if note_file.exists():
                    note_file.unlink()
                await self.send_text(f"【{safe_group}】喵内把集会码忘光光了喵~")
                return True, "全部删除成功", False
            
            # 处理指定行删除
            try:
                line_numbers = [int(num.strip()) for num in del_param.split(",") if num.strip().isdigit()]
                if not line_numbers:
                    raise ValueError("无效的行号")
            except:
                await self.send_text(f"【{safe_group}】出现了奇奇怪怪的错误喵~可以再尝试一次喵~")
                return False, "无效的行号格式", False
            
            if not note_file.exists():
                await self.send_text(f"【{safe_group}】集会码是空的喵~没人打猎嘛？")
                return True, "空文件", False
            
            with open(note_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            if not lines:
                await self.send_text(f"【{safe_group}】集会码是空的喵~没人打猎嘛？")
                return True, "空内容", False
            
            # 验证行号范围并排序（从大到小删除避免索引变化）
            valid_lines = sorted([num for num in line_numbers if 1 <= num <= len(lines)], reverse=True)
            if not valid_lines:
                await self.send_text(f"【{safe_group}】无效的行号喵~ 当前共有{len(lines)}条集会码喵！")
                return False, "无效行号范围", False
            
            # 删除指定行
            for num in valid_lines:
                del lines[num - 1]
            
            # 写入更新后的内容
            with open(note_file, "w", encoding="utf-8") as f:
                f.writelines(lines)
            
            # 准备响应内容
            remaining = len(lines)
            if remaining > 0:
                numbered_lines = [f"{i+1}. {line.strip()}\n" for i, line in enumerate(lines)]
                content = "".join(numbered_lines)
                response = f"【{safe_group}】成功删除了{len(valid_lines)}行集会码喵~剩余的集会码在这里喵：\n{content}"
            else:
                response = f"【{safe_group}】成功删除了{len(valid_lines)}行集会码喵~现在没有任何的集会码了喵~"
            
            await self.send_text(response)
            return True, "删除成功", False
        except Exception as e:
            error_msg = f"【{safe_group}】处理集会码时出错了喵：{str(e)}"
            await self.send_text(error_msg)
            return False, str(e), False
        
# ===== 插件注册 =====

@register_plugin
class MHWorldPlugin(BasePlugin):
    """怪物猎人:世界插件 - 集会码插件"""

    # 插件基本信息（必须填写）
    plugin_name = "mhwJH_plugin"
    plugin_description = "怪猎集会码插件"
    plugin_author = "倒过来的蛋糕蛋糕"
    enable_plugin = True
    config_file_name = "config.toml"
    dependencies = []
    python_dependencies = []
    
    config_section_descriptions = {
        "plugin": "插件基本信息",
        "storage": "集会码存储配置",
        "behavior": "插件行为配置",
    }
    
    # 配置Schema定义
    config_schema = {
        "plugin": {
            "enabled": ConfigField(type=bool, default=True, description="是否启用插件"),
            "command_TURN":ConfigField(type=bool, default=False, description="是否启用命令（与艾露猫指令相同'/a','/p','/d'）"),
            "config_version": ConfigField(type=str, default="1.2.0", description="配置文件版本，请不要随意更改")
        },
        "storage": {
            "data_dir": ConfigField(
                type=str, 
                default="data/mhw_jh", 
                description="集会码存储目录（相对或绝对路径）",
            ),
            "max_entries": ConfigField(
                type=int, 
                default=5, 
                description="每个群组保存的最大集会码数量",
            ),
            "file_prefix": ConfigField(
                type=str, 
                default="p_notepad", 
                description="集会码文件前缀",
            )
        },
        "behavior": {
            "enable_duplicate_check": ConfigField(
                type=bool, 
                default=True, 
                description="是否启用集会码重复检查"
            ),
            "enable_timestamp": ConfigField(
                type=bool, 
                default=True, 
                description="是否在集会码记录中添加时间戳（不会影响已经登录的集会码）"
            ),
        }
    }

    def get_plugin_components(self) -> List[Tuple[ComponentInfo, Type]]:
        """返回插件包含的组件列表"""
        components = []
        Command_TURN = self.get_config("plugin.command_TURN", True)
        components.append((MHWJHAction.get_action_info(), MHWJHAction))
        if Command_TURN:
            components.append((MHWJHRegisterCommand.get_command_info(), MHWJHRegisterCommand))
            components.append((MHWJHQueryCommand.get_command_info(), MHWJHQueryCommand))
            components.append((MHWJHDeleteCommand.get_command_info(), MHWJHDeleteCommand))
        return components
    
    #来点萝莉