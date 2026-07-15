package com.smartlegal.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.smartlegal.entity.User;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

/**
 * 用户Mapper
 */
public interface UserMapper extends BaseMapper<User> {

    /**
     * 根据用户名查询用户
     */
    @Select("SELECT * FROM sys_user WHERE username = #{username} AND deleted = 0")
    User findByUsername(@Param("username") String username);

    /**
     * 查询用户拥有的角色列表
     */
    @Select("SELECT r.role_code FROM sys_role r " +
            "INNER JOIN sys_user_role ur ON r.id = ur.role_id " +
            "WHERE ur.user_id = #{userId} AND r.status = 1")
    List<String> findRolesByUserId(@Param("userId") Long userId);

    /**
     * 查询用户拥有的权限列表
     */
    @Select("SELECT DISTINCT p.perm_code FROM sys_permission p " +
            "INNER JOIN sys_role_permission rp ON p.id = rp.permission_id " +
            "INNER JOIN sys_user_role ur ON rp.role_id = ur.role_id " +
            "WHERE ur.user_id = #{userId}")
    List<String> findPermissionsByUserId(@Param("userId") Long userId);
}
