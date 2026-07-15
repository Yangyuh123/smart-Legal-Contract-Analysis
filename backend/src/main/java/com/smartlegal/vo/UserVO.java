package com.smartlegal.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 用户信息VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UserVO {

    /** 用户ID */
    private Long id;

    /** 用户名 */
    private String username;

    /** 真实姓名 */
    private String realName;

    /** 邮箱 */
    private String email;

    /** 手机号 */
    private String phone;

    /** 头像URL */
    private String avatar;

    /** 状态：1-启用，0-禁用 */
    private Integer status;

    /** 最后登录时间 */
    private LocalDateTime lastLoginTime;

    /** 角色列表 */
    private List<String> roles;

    /** 权限列表 */
    private List<String> permissions;
}
