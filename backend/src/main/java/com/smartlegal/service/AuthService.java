package com.smartlegal.service;

import com.smartlegal.dto.LoginDTO;
import com.smartlegal.dto.RegisterDTO;
import com.smartlegal.vo.LoginVO;
import com.smartlegal.vo.UserVO;

/**
 * 认证服务接口
 */
public interface AuthService {

    /**
     * 用户登录
     * @param loginDTO 登录请求
     * @return 登录响应（含token和用户信息）
     */
    LoginVO login(LoginDTO loginDTO);

    /**
     * 用户注册
     * @param registerDTO 注册请求
     * @return 注册成功的用户信息
     */
    UserVO register(RegisterDTO registerDTO);

    /**
     * 刷新令牌
     * @param refreshToken 刷新令牌
     * @return 新的token对
     */
    LoginVO refresh(String refreshToken);

    /**
     * 获取当前登录用户信息
     * @return 当前用户信息
     */
    UserVO getCurrentUser();
}
