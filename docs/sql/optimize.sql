-- ============================================================
-- SmartLegal 数据库优化脚本 (optimize.sql)
-- ------------------------------------------------------------
-- 目的: 清理当前后端代码 **未实际使用** 的数据表，使数据库结构
--       与运行中的系统保持一致，降低维护成本与误用风险。
--
-- 使用方法:
--   mysql -u root -p smart_legal < optimize.sql
--
-- 重要说明（务必阅读）:
--   下列表在原始 init.sql 中已设计，但当前后端 (backend/) 代码
--   **没有任何 Entity / Mapper / SQL 引用**，属于“已设计未接入”状态：
--
--   表名                | 现状                                   | 相关功能后续接入方式
--   --------------------|----------------------------------------|--------------------------------
--   contract            | 无 Contract 实体/Mapper                 | 实现合同管理模块时重新启用
--   generation_record   | 生成走 FastAPI 代理, 未落库(内存/无持久化) | 实现“生成记忆持久化”时启用
--   compare_record      | 比对结果存于后端内存 ConcurrentHashMap    | 实现“比对历史”落库时启用
--   compare_diff        | 同上                                   | 同上
--   compliance_record   | 合规审查模块后端尚未实现                  | 实现合规审查模块时启用
--   compliance_issue    | 同上                                   | 同上
--
--   分析依据:
--   - grep 全后端未出现 contract / compliance / clause 相关引用
--   - CompareRecord / CompareDiff / GenerationRecord 实体已作为死代码删除
--   - ComparisonServiceImpl 使用内存存储; GenerationServiceImpl 仅代理 FastAPI
--
--   已确认 **仍在使用**、不可删除的表:
--     sys_user / sys_role / sys_user_role / sys_permission /
--     sys_role_permission / sys_notification / review_record /
--     review_risk / kb_document
--   (其中 sys_permission、sys_role_permission 通过
--    UserMapper.findPermissionsByUserId 驱动前端菜单权限)
-- ============================================================

USE smart_legal;

-- 关闭外键检查以便按任意顺序删除
SET FOREIGN_KEY_CHECKS = 0;

-- 1) 合规审查（后端未实现）
DROP TABLE IF EXISTS compliance_issue;
DROP TABLE IF EXISTS compliance_record;

-- 2) 合同比对（结果存于后端内存，未落库）
DROP TABLE IF EXISTS compare_diff;
DROP TABLE IF EXISTS compare_record;

-- 3) 合同生成记录（生成走 FastAPI 代理，未持久化）
DROP TABLE IF EXISTS generation_record;

-- 4) 合同管理（无对应后端模块，且上述表原本外键依赖它）
DROP TABLE IF EXISTS contract;

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================
-- 回滚提示:
--   若后续实现对应功能，请从 init.sql 中复制相应的 CREATE TABLE
--   语句重新建表，并补齐 backend 端的 Entity / Mapper / Service。
-- ============================================================
