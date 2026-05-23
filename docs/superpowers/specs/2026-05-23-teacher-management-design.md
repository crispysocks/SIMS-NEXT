# 教师管理模块设计方案

**日期**: 2026-05-23
**模块**: 教师管理（Teacher Management）

---

## 1. 整体架构

```
项目结构：
app/
├── api/v1/
│   └── teacher.py          # 教师模块路由
├── services/
│   └── teacher_service.py  # 业务逻辑
├── repositories/
│   └── teacher_repository.py # 数据访问
├── schemas/
│   └── teacher.py          # 请求/响应 Pydantic 模型
├── models/
│   └── teacher.py          # ORM 模型（SQLAlchemy）
├── core/
│   ├── database.py         # 数据库连接
│   └── config.py           # 配置管理
└── main.py                 # FastAPI 应用入口

配置文件：
.env                        # 数据库连接等敏感配置
.env.example                # 配置模板
pyproject.toml              # 项目依赖和元数据
```

**分层职责**：
- **api/v1**: 处理 HTTP 请求/响应，路由定义
- **schemas**: 定义 API 的输入输出模型（Pydantic）
- **services**: 业务逻辑，不直接接触数据库
- **repositories**: 数据访问层，直接操作数据库
- **core**: 数据库连接、配置管理等基础设施

---

## 2. 数据模型

**教师表（teachers）**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键，自增 |
| teacher_no | str(20) | 工号，唯一，格式：字母开头+数字，6-20位 |
| name | str(50) | 姓名，2-20字符 |
| gender | str(10) | 性别，仅允许：男、女 |
| entry_date | date | 入职时间 |
| is_deleted | bool | 逻辑删除标记，默认 False |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

**索引**：
- `teacher_no` 唯一索引
- `is_deleted` 普通索引

---

## 3. API 设计

**基础路径**：`/api/v1`

| 方法 | 路径 | 说明 | 请求体 | 响应 |
|------|------|------|--------|------|
| GET | /teachers | 获取教师列表（分页+筛选） | query params | 分页结果 |
| POST | /teachers | 创建教师 | TeacherCreate | TeacherDetail |
| GET | /teachers/{teacher_no} | 获取教师详情 | - | TeacherDetail |
| PUT | /teachers/{teacher_no} | 更新教师信息 | TeacherUpdate | TeacherDetail |
| DELETE | /teachers/{teacher_no} | 逻辑删除教师 | - | 204 No Content |

**查询参数**（GET /teachers）：
- `page`: 页码，默认1
- `page_size`: 每页数量，默认20
- `name`: 姓名筛选（模糊匹配）
- `teacher_no`: 工号筛选（精确匹配）

**响应格式**：
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

---

## 4. 字段校验规则

| 字段 | 规则 |
|------|------|
| teacher_no | 必填，格式：字母开头+数字，6-20位，唯一 |
| name | 必填，2-20字符 |
| gender | 必填，仅允许：男、女 |
| entry_date | 必填，日期格式 |

**错误响应格式**：
```json
{
  "detail": [
    {"field": "name", "message": "姓名不能为空"},
    {"field": "teacher_no", "message": "工号必须以字母开头"}
  ]
}
```

---

## 5. 服务层业务逻辑

**TeacherService 主要方法**：

```python
# 创建教师
create_teacher(data: TeacherCreate) -> TeacherDetail
  1. 校验工号唯一性
  2. 创建教师记录
  3. 返回创建结果

# 获取教师列表
get_teachers(page, page_size, name, teacher_no) -> PagedResult[TeacherDetail]
  1. 构建查询条件（包括 is_deleted=False）
  2. 姓名模糊匹配，工号精确匹配
  3. 分页查询
  4. 返回分页结果

# 获取教师详情
get_teacher(teacher_no: str) -> TeacherDetail | None
  1. 查询教师（is_deleted=False）
  2. 不存在则抛出 404

# 更新教师
update_teacher(teacher_no: str, data: TeacherUpdate) -> TeacherDetail
  1. 校验教师存在
  2. 校验工号唯一性（如果改了工号）
  3. 更新记录
  4. 返回更新结果

# 删除教师（逻辑删除）
delete_teacher(teacher_no: str) -> None
  1. 校验教师存在
  2. 设置 is_deleted=True
```

---

## 6. 依赖包

```
fastapi
uvicorn
sqlalchemy
pydantic
python-dotenv
pymysql
```
（已存在于项目依赖中）

---

## 7. 实现顺序

1. `models/teacher.py` - ORM 模型
2. `schemas/teacher.py` - Pydantic 模型
3. `repositories/teacher_repository.py` - 数据访问层
4. `services/teacher_service.py` - 业务逻辑层
5. `api/v1/teacher.py` - 路由层
6. `main.py` - 注册路由
7. `scripts/create_tables.sql` - 更新数据库脚本