package com.smartlegal.service.impl;

import com.smartlegal.common.BusinessException;
import com.smartlegal.dto.LoginDTO;
import com.smartlegal.dto.RegisterDTO;
import com.smartlegal.entity.User;
import com.smartlegal.mapper.UserMapper;
import com.smartlegal.security.JwtTokenProvider;
import com.smartlegal.service.AuthService;
import com.smartlegal.vo.LoginVO;
import com.smartlegal.vo.UserVO;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 认证服务实现
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class AuthServiceImpl implements AuthService {

    private final UserMapper userMapper;
    private final JwtTokenProvider jwtTokenProvider;
    private final PasswordEncoder passwordEncoder;

    @Override
    public LoginVO login(LoginDTO loginDTO) {
        // 查询用户
        User user = userMapper.findByUsername(loginDTO.getUsername());
        if (user == null) {
            throw new BusinessException(401, "用户名或密码错误");
        }
        if (user.getStatus() != null && user.getStatus() == 0) {
            throw new BusinessException(403, "账号已被禁用，请联系管理员");
        }

        // 校验密码
        if (!passwordEncoder.matches(loginDTO.getPassword(), user.getPassword())) {
            throw new BusinessException(401, "用户名或密码错误");
        }

        // 更新最后登录时间
        user.setLastLoginTime(LocalDateTime.now());
        userMapper.updateById(user);

        // 查询角色和权限
        List<String> roles = userMapper.findRolesByUserId(user.getId());
        List<String> permissions = userMapper.findPermissionsByUserId(user.getId());

        // 生成token
        String accessToken = jwtTokenProvider.generateAccessToken(user.getId(), user.getUsername(), roles, permissions);
        String refreshToken = jwtTokenProvider.generateRefreshToken(user.getId(), user.getUsername());

        // 构建响应
        UserVO userVO = buildUserVO(user, roles, permissions);

        return LoginVO.builder()
                .token(accessToken)
                .refreshToken(refreshToken)
                .user(userVO)
                .build();
    }

    @Override
    @Transactional
    public UserVO register(RegisterDTO registerDTO) {
        // 检查用户名是否已存在
        User existing = userMapper.findByUsername(registerDTO.getUsername());
        if (existing != null) {
            throw new BusinessException(400, "用户名已存在");
        }

        // 创建新用户
        User user = new User();
        user.setUsername(registerDTO.getUsername());
        user.setPassword(passwordEncoder.encode(registerDTO.getPassword()));
        user.setRealName(registerDTO.getRealName());
        user.setEmail(registerDTO.getEmail());
        user.setStatus(1);
        user.setLastLoginTime(LocalDateTime.now());
        userMapper.insert(user);

        log.info("新用户注册成功: {}", user.getUsername());

        List<String> roles = userMapper.findRolesByUserId(user.getId());
        List<String> permissions = userMapper.findPermissionsByUserId(user.getId());

        return buildUserVO(user, roles, permissions);
    }

    @Override
    public LoginVO refresh(String refreshToken) {
        if (!jwtTokenProvider.validateToken(refreshToken)) {
            throw new BusinessException(401, "刷新令牌无效或已过期");
        }

        Long userId = jwtTokenProvider.getUserId(refreshToken);
        User user = userMapper.selectById(userId);
        if (user == null) {
            throw new BusinessException(401, "用户不存在");
        }
        if (user.getStatus() != null && user.getStatus() == 0) {
            throw new BusinessException(403, "账号已被禁用");
        }

        List<String> roles = userMapper.findRolesByUserId(userId);
        List<String> permissions = userMapper.findPermissionsByUserId(userId);

        String newAccessToken = jwtTokenProvider.generateAccessToken(user.getId(), user.getUsername(), roles, permissions);
        String newRefreshToken = jwtTokenProvider.generateRefreshToken(user.getId(), user.getUsername());

        UserVO userVO = buildUserVO(user, roles, permissions);

        return LoginVO.builder()
                .token(newAccessToken)
                .refreshToken(newRefreshToken)
                .user(userVO)
                .build();
    }

    @Override
    public UserVO getCurrentUser() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication == null || !authentication.isAuthenticated()) {
            throw new BusinessException(401, "未登录");
        }

        Long userId = (Long) authentication.getPrincipal();
        User user = userMapper.selectById(userId);
        if (user == null) {
            throw new BusinessException(404, "用户不存在");
        }

        List<String> roles = userMapper.findRolesByUserId(userId);
        List<String> permissions = userMapper.findPermissionsByUserId(userId);

        return buildUserVO(user, roles, permissions);
    }

    /**
     * 构建UserVO
     */
    private UserVO buildUserVO(User user, List<String> roles, List<String> permissions) {
        return UserVO.builder()
                .id(user.getId())
                .username(user.getUsername())
                .realName(user.getRealName())
                .email(user.getEmail())
                .phone(user.getPhone())
                .avatar(user.getAvatar())
                .status(user.getStatus())
                .lastLoginTime(user.getLastLoginTime())
                .roles(roles)
                .permissions(permissions)
                .build();
    }
}
