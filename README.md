# MindMap

支持 20000+ 节点、2 人实时协同编辑的思维导图应用。

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python / FastAPI / WebSocket |
| 数据库 | SQLite (WAL 模式, aiosqlite) |
| 前端 | Vue 3 / Pinia / Canvas 2D |
| 构建 | Vite |
| 容器 | Docker (多阶段构建) |
| 认证 | JWT (HS256) + bcrypt 密码哈希 |

## 项目结构

```
├── config.yaml              # 端口、数据库路径、JWT 密钥配置
├── run.py                   # 启动入口
├── requirements.txt         # Python 依赖
├── Dockerfile               # 多阶段构建
├── docker-compose.yml       # Docker Compose 配置
├── backend/
│   ├── app.py               # FastAPI 工厂，挂载路由和静态文件
│   ├── config.py            # 配置加载 (YAML + 环境变量)
│   ├── auth.py              # JWT 创建/验证、密码哈希、FastAPI 依赖
│   ├── db.py                # SQLite 连接与初始化（含迁移）
│   ├── routers/
│   │   ├── auth.py          # 注册、登录、令牌刷新、登出
│   │   ├── maps.py          # 导图 CRUD、同步、认领、历史
│   │   ├── nodes.py         # 节点 CRUD、历史、回滚、锁
│   │   └── teams.py         # 团队与邀请管理
│   ├── services/            # 业务逻辑层
│   │   ├── auth_service.py
│   │   ├── map_service.py
│   │   ├── node_service.py  # 节点操作、历史记录、锁管理
│   │   ├── team_service.py
│   │   └── permission_service.py
│   └── ws/
│       ├── manager.py       # WebSocket 房间连接管理
│       └── handler.py       # WebSocket 消息处理
└── frontend/
    ├── src/
    │   ├── App.vue
    │   ├── pages/           # 登录、注册、主页、编辑器、团队页面
    │   ├── stores/          # Pinia 状态管理 (mindmap, auth, teams)
    │   ├── composables/     # useSync、useWebSocket、useUndo
    │   ├── components/      # Canvas 画布、工具栏、小地图、历史面板
    │   ├── services/api.ts  # API 请求封装、401 自动刷新
    │   └── utils/           # 树操作、布局算法
    └── dist/                # 构建产物 (被 Python 托管)
```

## 快速开始

### 本地运行

```bash
# 1. 安装 Python 依赖
pip install -r requirements.txt

# 2. 构建前端
cd frontend
npm install
npm run build
cd ..

# 3. 启动
python run.py
```

浏览器访问 `http://localhost:8080`。

### 开发模式

```bash
# 终端 1：启动后端
python run.py

# 终端 2：启动前端开发服务器（自动代理 /api 和 /ws 到 localhost:8080）
cd frontend
npm run dev
```

### Docker

```bash
# 构建镜像
docker build -t mindmap .

# 默认端口 8080
docker run -p 8080:8080 -v ./data:/app/data mindmap

# 自定义端口
docker run -e MINDMAP_PORT=3000 -p 3000:3000 -v ./data:/app/data mindmap

# 推荐使用 docker-compose（可配置 JWT_SECRET）
docker-compose up
```

## 配置

通过 `config.yaml` 或环境变量配置：

| 配置项 | config.yaml | 环境变量 | 默认值 |
|--------|-------------|----------|--------|
| 端口 | `port` | `MINDMAP_PORT` | `8080` |
| 数据库路径 | `database` | `MINDMAP_DATABASE` | `./data/mindmap.db` |
| JWT 密钥 | `jwt_secret` | `MINDMAP_JWT_SECRET` | `CHANGE-ME-IN-PRODUCTION` |

环境变量优先于 `config.yaml`。Access Token 有效期 30 分钟，Refresh Token 有效期 30 天。

## 功能特性

### 核心编辑

- 思维导图 Canvas 2D 渲染，支持 20000+ 节点
- 单击已选中节点直接进入编辑模式（也支持双击、F2、空格键）
- Tab 添加子节点，Enter 添加同级节点，Delete 删除节点
- 鼠标拖拽平移画布，滚轮缩放
- 节点折叠/展开
- 小地图快速导航

### 撤销操作

- Ctrl+Z / Cmd+Z 撤销最近操作（最多保留 100 步）
- 工具栏提供撤销按钮
- 支持撤销创建、删除（含完整子树恢复）、内容编辑

### 协同编辑

- 两种同步机制：REST 轮询（当前启用）和 WebSocket（已实现）
- 节点编辑锁：编辑节点时自动加锁，其他用户看到红色虚线边框和编辑者名称
- 锁自动过期（5 分钟），编辑完成后自动释放
- Last-Write-Wins 冲突处理策略

### 编辑历史

- 所有节点操作（创建、编辑、删除）自动记录历史
- 记录操作者、时间、变更前后内容
- 删除操作保存完整子树快照，支持完整恢复
- 右键节点查看单节点历史，或查看整个导图历史
- 支持回滚到任意历史版本

### 编辑者信息

- 每个节点记录最后编辑者和编辑时间
- 鼠标悬停节点时显示编辑者名称和时间

### 用户与权限

- 用户注册/登录（JWT 认证）
- 团队管理：创建团队、邀请成员
- 角色权限：Owner > Admin > Editor > Viewer
- 个人导图仅本人访问，团队导图按角色控制

## API

### 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 注册（无需认证） |
| POST | `/api/auth/login` | 登录（无需认证） |
| POST | `/api/auth/refresh` | 刷新令牌 |
| POST | `/api/auth/logout` | 登出 |
| GET | `/api/auth/me` | 获取当前用户信息 |

### 导图

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/maps` | 列出可访问的导图 |
| POST | `/api/maps` | 创建导图 |
| GET | `/api/maps/{id}` | 获取导图及全部节点 |
| DELETE | `/api/maps/{id}` | 删除导图（仅 Owner） |
| GET | `/api/maps/{id}/sync?since={ver}` | 增量同步（含锁状态） |
| POST | `/api/maps/{id}/claim` | 认领无主导图 |
| GET | `/api/maps/{id}/history` | 获取导图操作历史 |

### 节点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/maps/{id}/nodes` | 创建节点 |
| PUT | `/api/maps/{id}/nodes/{nid}` | 更新节点 |
| DELETE | `/api/maps/{id}/nodes/{nid}` | 删除节点 |
| GET | `/api/maps/{id}/nodes/{nid}/history` | 获取节点历史 |
| POST | `/api/maps/{id}/nodes/{nid}/history/{hid}/rollback` | 回滚到指定历史 |
| POST | `/api/maps/{id}/nodes/{nid}/lock` | 获取编辑锁 |
| DELETE | `/api/maps/{id}/nodes/{nid}/lock` | 释放编辑锁 |

### WebSocket

| 路径 | 说明 |
|------|------|
| `/ws/{map_id}?token=...` | 实时协同（通过 query 参数传递 JWT） |

消息格式：

```json
{
  "type": "node:create | node:update | node:delete | node:move",
  "data": { "id": "...", "parent_id": "...", "content": "...", "changes": {} },
  "version": 1
}
```

## 键盘快捷键

| 按键 | 操作 |
|------|------|
| Tab | 添加子节点 |
| Enter | 添加同级节点 |
| Delete / Backspace | 删除节点 |
| F2 / Space | 编辑节点文本 |
| Ctrl+Z / Cmd+Z | 撤销 |
| 单击已选中节点 | 进入编辑 |
| 双击节点 | 编辑节点文本 |
| 右键节点 | 查看历史 |
| 鼠标拖拽空白 | 平移画布 |
| 滚轮 | 缩放 |

## 数据库 Schema

8 张核心表：

- `maps` — 导图元数据（含 owner_id、team_id）
- `nodes` — 节点数据（含 last_edited_by/name/at）
- `change_log` — 变更日志（用于增量同步）
- `node_history` — 完整操作历史（含变更前后内容和子树快照）
- `node_locks` — 节点编辑锁
- `users` — 用户信息
- `refresh_tokens` — 刷新令牌
- `teams` / `team_members` / `team_invitations` — 团队与邀请

## 性能策略

- Canvas 2D 渲染，非 DOM
- 视口裁剪：仅绘制可见区域内的节点
- 折叠子树不参与布局和渲染
- 后端一次查询返回扁平节点列表，前端构建树
- SQLite WAL 模式支持并发读写
- 增量同步：仅传输版本号之后的变更
