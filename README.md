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

## 项目结构

```
├── config.yaml              # 端口、数据库路径配置
├── run.py                   # 启动入口
├── requirements.txt         # Python 依赖
├── Dockerfile               # 多阶段构建
├── backend/
│   ├── app.py               # FastAPI 工厂，挂载路由和静态文件
│   ├── config.py            # 配置加载 (YAML + 环境变量)
│   ├── db.py                # SQLite 连接与初始化
│   ├── models.py            # 数据模型
│   ├── routers/maps.py      # REST API: 导图 CRUD
│   ├── ws/manager.py        # WebSocket 房间连接管理
│   ├── ws/handler.py        # WebSocket 消息处理
│   └── services/            # 业务逻辑层
└── frontend/
    ├── src/
    │   ├── App.vue           # 导图列表 / 编辑器入口
    │   ├── stores/mindmap.ts # 状态管理
    │   ├── composables/      # WebSocket、布局 composable
    │   ├── components/       # Canvas 画布、工具栏、小地图
    │   └── utils/            # 树操作、布局算法
    └── dist/                 # 构建产物 (被 Python 托管)
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

### Docker

```bash
# 构建镜像
docker build -t mindmap .

# 默认端口 8080
docker run -p 8080:8080 -v ./data:/app/data mindmap

# 自定义端口
docker run -e MINDMAP_PORT=3000 -p 3000:3000 -v ./data:/app/data mindmap
```

## 配置

通过 `config.yaml` 或环境变量配置：

| 配置项 | config.yaml | 环境变量 | 默认值 |
|--------|-------------|----------|--------|
| 端口 | `port` | `MINDMAP_PORT` | `8080` |
| 数据库路径 | `database` | `MINDMAP_DATABASE` | `./data/mindmap.db` |

环境变量优先于 `config.yaml`。

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/maps` | 列出所有导图 |
| POST | `/api/maps` | 创建导图 (`{"name": "..."}`) |
| GET | `/api/maps/{id}` | 获取导图及全部节点 |
| DELETE | `/api/maps/{id}` | 删除导图 |
| WS | `/ws/{map_id}` | 实时协同 WebSocket |

节点操作通过 WebSocket 进行，消息格式：

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
| 双击节点 | 编辑节点文本 |
| 鼠标拖拽空白 | 平移画布 |
| 滚轮 | 缩放 |

## 协同机制

采用操作广播 + Last-Write-Wins 策略。服务端为每个导图维护版本号，客户端通过 `client_id` 跳过自己发出的广播。两个浏览器标签页打开同一导图即可测试实时协同。

## 性能策略

- Canvas 2D 渲染，非 DOM
- 视口裁剪：仅绘制可见区域内的节点
- 折叠子树不参与布局和渲染
- 后端一次查询返回扁平节点列表，前端构建树
- SQLite WAL 模式支持并发读写
