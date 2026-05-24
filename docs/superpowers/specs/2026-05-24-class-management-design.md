# 班级管理模块设计

## 1. 概述

班级管理模块提供班级的 CRUD 操作，支持按班级编号和名称筛选查询。

## 2. 数据模型

### Class 模型

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键，自增 |
| class_no | String(50) | 班级编号，唯一，非空 |
| class_name | String(100) | 班级名称，非空 |
| head_teacher_no | String(50) | 班主任工号，唯一，非空 |
| is_deleted | Boolean | 软删除标记，默认 false |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### 索引

- class_no：唯一索引
- head_teacher_no：唯一索引

## 3. 校验规则

- class_no：必填，非空字符串
- class_name：必填，非空
- head_teacher_no：必填，对应教师需存在且未担任其他班级班主任（代码验证）

## 4. API 设计

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /classes | 获取班级列表（支持 class_no、class_name 模糊筛选） |
| POST | /classes | 创建班级 |
| GET | /classes/{id} | 获取班级详情 |
| PUT | /classes/{id} | 更新班级 |
| DELETE | /classes/{id} | 逻辑删除班级 |

### 查询参数

- GET /classes
  - class_no：班级编号（模糊匹配）
  - class_name：班级名称（模糊匹配）

## 5. 业务逻辑

### 删除逻辑

- 软删除班级（is_deleted = true）
- 级联清空属于该班级的学生的 class_no 字段

### 班主任唯一性

- 每个班主任只能担任一个班级
- 创建/更新时验证 head_teacher_no 未被其他班级使用

### 模糊搜索

- class_no / class_name 使用 `LIKE %keyword%` 实现模糊匹配

## 6. 技术栈

- 框架：FastAPI + SQLAlchemy + Pydantic v2
- 数据库：MySQL
- 软删除模式

## 7. 文件结构

```
app/
├── models/
│   └── class.py              # Class ORM 模型
├── schemas/
│   └── class.py              # ClassCreate, ClassUpdate, ClassDetail, PaginatedClasses
├── repositories/
│   └── class_repository.py   # 数据访问层
├── services/
│   └── class_service.py      # 业务逻辑层
└── api/v1/
    └── class.py              # API 路由
```