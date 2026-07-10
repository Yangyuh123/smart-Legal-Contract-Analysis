/**
 * 用户与权限相关类型定义（与后端 UserVO 对齐）
 */

/** 用户信息 */
export interface UserInfo {
  id: number
  username: string
  email: string
  phone: string
  avatar: string
  realName: string
  /** 角色编码列表，如 ["admin","user"] */
  roles: string[]
  /** 权限编码列表，如 ["review:create","review:view"] */
  permissions: string[]
  createTime: string
  updateTime: string
}

/** 登录请求参数 */
export interface LoginRequest {
  username: string
  password: string
}

/** 注册请求参数 */
export interface RegisterRequest {
  username: string
  password: string
  email: string
  realName: string
  phone: string
}
