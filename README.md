# MaiBot-MHWJH-Plugin
这是一个提供给麦麦bot的怪猎集会码插件，包括智能登记、查询、删除集会码，支持多群组隔离。


# 简介
<img width="369" height="369" alt="WXSV7vwlfQlD60J thumb 1000_0" src="https://github.com/user-attachments/assets/6c9e5db8-77e5-4b13-b14d-c88ffe6f1e48" />

咱是发现挺多群都有打怪猎的人，在专门打怪猎的群中，也有人使用了qq官方的艾露猫bot。

突发奇想，为什么不能让麦麦来帮忙登记？

于是在几个昼夜的石山堆积后，终于写出了这堆石山代码！😈😈😈


# 主要功能
- 🏷️ 智能判断指令：通过“集会码”、“集会”关键词，自动判断指令

    只需关键词，就可以通过对话，判断指令

  
- 🎮 集会码登记：快速登记当前狩猎集会码

    智能登记集会码，自动添加时间戳

    <img width="1075" height="230" alt="image" src="https://github.com/user-attachments/assets/5c26e202-2905-4080-a641-8cc4a09c6892" />

    并且当集会码数量达到最大时，自动删除最旧的集会码
    
    
- 🔍 集会码查询：随时查看群内保存的集会码

    按列展示已经登记的集会码
  
    <img width="1074" height="302" alt="image" src="https://github.com/user-attachments/assets/e085a219-f96b-4867-9a99-f2abe50738f5" />
  

- 🗑️ 集会码管理：删除单条或全部集会码

    指定删除一行、多行、全部集会码

    <img width="1095" height="719" alt="image" src="https://github.com/user-attachments/assets/4cd8f331-5bfd-4849-bc50-33e621ef37d7" />

    <img width="1065" height="234" alt="image" src="https://github.com/user-attachments/assets/21e4f91a-e63e-4d66-bac2-debe30657ea1" />
    

- ⚙️ 配置项：自定义存储位置、最大记录数等

    麦麦插件接口，自动生成配置文件
  

- 🔍 数据独立：每个群组独立存储集会码

    文件储存群集会码，群组独立
  

- 📅 时间戳记录：记录集会码创建时间（可选）

    可以开关的时间戳登记，简洁/美观二选一
  

- 🔄 重复检查：避免重复登记相同集会码（可选）

    可以开关的重复集会码登记，防蠢
  

# 安装步骤与配置
你只需要一台配置好的麦麦0.8.0以上版本

将插件放入插件文件夹，可以是本体根目录/plugins或者src/plugins/built_in

插件首次运行时会自动生成config.toml配置文件，您可以根据需要修改以下设置：


# 可选的配置项

```toml
data_dir = "data/mhw_jh"  # 集会码存储目录

max_entries = 5  # 每个群组最大集会码数量

file_prefix = "p_notepad"  # 集会码文件前缀

enable_duplicate_check = true  # 启用集会码重复检查

enable_timestamp = true  # 在记录中添加时间戳

```


# 依赖
- 配置好的麦麦0.9.1以上版本

- python 3.10

# 更新日志
2025年8月27日：1.2.0更新，
            尝试修复等号出现在集会码第一位，导致无法正确登记的问题；
            增加了command指令，使用和艾露猫bot类似的指令，通过/a、/p、/d指令来跳过llm，直接登记、查询、删除集会码
            增加了对maibot0.9.1和0.10版本的兼容

# 未来计划
- 为怪猎荒野的群组常驻集会码做适配


# 作者与版本

- 插件作者：倒过来的蛋糕蛋糕

- 插件版本：1.2.0
