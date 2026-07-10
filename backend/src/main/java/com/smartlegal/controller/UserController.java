package com.smartlegal.controller;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.smartlegal.common.PageResult;
import com.smartlegal.common.Result;
import com.smartlegal.service.UserService;
import com.smartlegal.vo.UserVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

/**
 * 用户控制器 —— 暴露 sys_user 数据供前端用户管理页使用
 */
@Slf4j
@RestController
@RequestMapping("/api/v1/users")
@RequiredArgsConstructor
@Tag(name = "用户管理", description = "系统用户的查询")
public class UserController {

    private final UserService userService;

    @GetMapping
    @Operation(summary = "分页查询用户列表")
    public Result<PageResult<UserVO>> list(
            @Parameter(description = "页码") @RequestParam(defaultValue = "1") int page,
            @Parameter(description = "每页大小") @RequestParam(defaultValue = "10") int size,
            @Parameter(description = "关键词(用户名/姓名)") @RequestParam(required = false) String keyword) {
        Page<UserVO> pageResult = userService.listUsers(page, size, keyword);
        return Result.success(PageResult.of(
                pageResult.getRecords(),
                pageResult.getTotal(),
                pageResult.getCurrent(),
                pageResult.getSize()
        ));
    }

    @GetMapping("/{id}")
    @Operation(summary = "获取用户详情")
    public Result<UserVO> detail(@Parameter(description = "用户ID") @PathVariable Long id) {
        UserVO userVO = userService.getUserById(id);
        return Result.success(userVO);
    }
}
