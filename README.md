# MaiBot-MHWJH-Plugin
这是一个提供给麦麦bot的怪猎集会码插件，包括智能登记、查询、删除集会码，支持多群组隔离。


# 简介
<img width="369" height="369" alt="WXSV7vwlfQlD60J thumb 1000_0" src="https://github.com/user-attachments/assets/6c9e5db8-77e5-4b13-b14d-c88ffe6f1e48" />

咱是发现挺多群都有打怪猎的人，在专门打怪猎的群中，也有人使用了qq官方的艾露猫bot。突发奇想


# 主要功能
- 🎮 集会码登记：快速登记当前狩猎集会码

- 🔍 集会码查询：随时查看群内保存的集会码

- 🗑️ 集会码管理：删除单条或全部集会码

- ⚙️ 配置项：自定义存储位置、最大记录数等

- 🛡️ 数据独立：每个群组独立存储集会码

- 📅 时间戳记录：记录集会码创建时间（可选）

- 🔄 重复检查：避免重复登记相同集会码（可选）


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
- 配置好的麦麦0.8.0以上版本

- python 3.10


# 作者与版本

- 插件作者：倒过来的蛋糕蛋糕

- 插件版本：1.1.0
