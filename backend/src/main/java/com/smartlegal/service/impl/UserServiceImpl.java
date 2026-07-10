package com.smartlegal.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.smartlegal.common.BusinessException;
import com.smartlegal.entity.User;
import com.smartlegal.mapper.UserMapper;
import com.smartlegal.service.UserService;
import com.smartlegal.vo.UserVO;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 用户服务实现
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class UserServiceImpl implements UserService {

    private final UserMapper userMapper;

    @Override
    public Page<UserVO> listUsers(int page, int size, String keyword) {
        LambdaQueryWrapper<User> wrapper = new LambdaQueryWrapper<>();
        if (keyword != null && !keyword.isBlank()) {
            wrapper.like(User::getUsername, keyword)
                   .or()
                   .like(User::getRealName, keyword)
                   .or()
                   .like(User::getEmail, keyword);
        }
        wrapper.orderByDesc(User::getCreateTime);

        Page<User> pageResult = userMapper.selectPage(Page.of(page, size), wrapper);

        // 转换为VO
        Page<UserVO> voPage = new Page<>(page, size, pageResult.getTotal());
        List<UserVO> voList = pageResult.getRecords().stream().map(user -> {
            List<String> roles = userMapper.findRolesByUserId(user.getId());
            List<String> permissions = userMapper.findPermissionsByUserId(user.getId());
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
        }).toList();
        voPage.setRecords(voList);

        return voPage;
    }

    @Override
    public UserVO getUserById(Long id) {
        User user = userMapper.selectById(id);
        if (user == null) {
            throw new BusinessException(404, "用户不存在");
        }
        List<String> roles = userMapper.findRolesByUserId(id);
        List<String> permissions = userMapper.findPermissionsByUserId(id);
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

    @Override
    public User findByUsername(String username) {
        return userMapper.findByUsername(username);
    }

    @Override
    public void updateUser(Long id, User user) {
        User existing = userMapper.selectById(id);
        if (existing == null) {
            throw new BusinessException(404, "用户不存在");
        }
        user.setId(id);
        userMapper.updateById(user);
    }

    @Override
    public List<String> getUserRoles(Long userId) {
        return userMapper.findRolesByUserId(userId);
    }

    @Override
    public List<String> getUserPermissions(Long userId) {
        return userMapper.findPermissionsByUserId(userId);
    }
}
