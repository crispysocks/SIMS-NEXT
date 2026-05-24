# 学生信息管理模块设计方案

**日期**: 2026-05-23
**模块**: 学生信息管理（Student Management）

---

## 1. 整体架构

```
项目结构：
app/
├── api/
│   └── v1/
│       └── student.py      # 学生模块路由
├── services/
│   └── student_service.py  # 业务逻辑
├── repositories/
│   └── student_repository.py # 数据访问
├── schemas/
│   └── student.py          # 请求/响应 Pydantic 模型
├── models/
│   └── student.py          # ORM 模型（SQLAlchemy）
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

**学生表（students）**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键，自增 |
| student_no | str(20) | 学号，唯一，格式：字母开头+数字，6-20位 |
| name | str(50) | 姓名，2-20字符 |
| gender | str(10) | 性别，仅允许：男、女 |
| age | int | 年龄，6-100 |
| native_place | str(100) | 籍贯，可选 |
| class_id | int | 班级ID，无外键约束，应用层关联 |
| enrollment_date | date | 入学时间 |
| is_deleted | bool | 逻辑删除标记，默认 False |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

**索引**：
- `student_no` 唯一索引
- `class_id` 普通索引
- `is_deleted` 普通索引

**说明**：数据库层面不设置外键约束，班级与学生的关联通过 `class_id` 字段在应用层处理。逻辑删除更灵活。

---

## 3. API 设计

**基础路径**：`/api/v1`

| 方法 | 路径 | 说明 | 请求体 | 响应 |
|------|------|------|--------|------|
| GET | /students | 获取学生列表（分页+筛选） | query params | 分页结果 |
| POST | /students | 创建学生 | StudentCreate | StudentDetail |
| GET | /students/{student_no} | 获取学生详情 | - | StudentDetail |
| PUT | /students/{student_no} | 更新学生信息 | StudentUpdate | StudentDetail |
| DELETE | /students/{student_no} | 逻辑删除学生 | - | 204 No Content |

**查询参数**（GET /students）：
- `page`: 页码，默认1
- `page_size`: 每页数量，默认20
- `name`: 姓名筛选（模糊匹配）
- `student_no`: 学号筛选（精确匹配）
- `class_id`: 班级筛选

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
| student_no | 必填，格式：字母开头+数字，6-20位，唯一 |
| name | 必填，2-20字符 |
| gender | 必填，仅允许：男、女 |
| age | 必填，6-100 |
| native_place | 选填，最大100字符 |
| class_id | 选填，引用班级存在性由应用层校验 |
| enrollment_date | 必填，日期格式 |

**错误响应格式**：
```json
{
  "detail": [
    {"field": "name", "message": "姓名不能为空"},
    {"field": "age", "message": "年龄必须在6-100之间"}
  ]
}
```

---

## 5. 服务层业务逻辑

**StudentService 主要方法**：

```python
# 创建学生
create_student(data: StudentCreate) -> StudentDetail
  1. 校验学号唯一性
  2. 校验班级存在（如果提供了class_id）
  3. 创建学生记录
  4. 返回创建结果

# 获取学生列表
get_students(page, page_size, name, student_no, class_id) -> PagedResult[StudentDetail]
  1. 构建查询条件（包括 is_deleted=False）
  2. 姓名模糊匹配，学号精确匹配
  3. 分页查询
  4. 返回分页结果

# 获取学生详情
get_student(student_no: str) -> StudentDetail | None
  1. 查询学生（is_deleted=False）
  2. 不存在则抛出 404

# 更新学生
update_student(student_no: str, data: StudentUpdate) -> StudentDetail
  1. 校验学生存在
  2. 校验学号唯一性（如果改了学号）
  3. 更新记录
  4. 返回更新结果

# 删除学生（逻辑删除）
delete_student(student_no: str) -> None
  1. 校验学生存在
  2. 设置 is_deleted=True
```

**成绩联动逻辑**：
- 查询成绩时自动过滤已删除学生的成绩（应用层处理）
- 删除学生时无需修改成绩表，只需确保查询时过滤

---

## 6. 项目配置

**数据库连接**：通过 `.env` 文件管理，不硬编码
```env
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/sims
```

**配置加载**：使用 `python-dotenv` 读取环境变量

---

## 7. 依赖包

```
fastapi
uvicorn
sqlalchemy
pydantic
python-dotenv
pymysql
```

---

## 8. 实现顺序

1. `core/config.py` - 配置管理
2. `core/database.py` - 数据库连接
3. `models/student.py` - ORM 模型
4. `schemas/student.py` - Pydantic 模型
5. `repositories/student_repository.py` - 数据访问层
6. `services/student_service.py` - 业务逻辑层
7. `api/v1/student.py` - 路由层
8. `main.py` - 应用入口