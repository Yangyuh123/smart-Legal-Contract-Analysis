package com.smartlegal.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 登录响应VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class LoginVO {

    /** JWT访问令牌 */
    private String token;

    /** 刷新令牌 */
    private String refreshToken;

    /** 用户基本信息 */
    private UserVO user;
}
