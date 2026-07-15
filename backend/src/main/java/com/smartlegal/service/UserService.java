package com.smartlegal.service;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.smartlegal.entity.User;
import com.smartlegal.vo.UserVO;

import java.util.List;

/**
 * 用户服务接口
 */
public interface UserService {

    /**
     * 分页查询用户列表
     * @param page 页码
     * @param size 每页大小
     * @param keyword 搜索关键字
     * @return 分页结果
     */
    Page<UserVO> listUsers(int page, int size, String keyword);

    /**
     * 根据ID获取用户
     * @param id 用户ID
     * @return 用户信息
     */
    UserVO getUserById(Long id);

    /**
     * 根据用户名查询用户实体
     * @param username 用户名
     * @return 用户实体，未找到返回null
     */
    User findByUsername(String username);

    /**
     * 更新用户信息
     * @param id 用户ID
     * @param user 更新的用户字段
     */
    void updateUser(Long id, User user);

    /**
     * 查询用户的角色列表
     * @param userId 用户ID
     * @return 角色编码列表
     */
    List<String> getUserRoles(Long userId);

    /**
     * 查询用户的权限列表
     * @param userId 用户ID
     * @return 权限编码列表
     */
    List<String> getUserPermissions(Long userId);
}
