package com.smartlegal.controller;

import com.smartlegal.common.Result;
import com.smartlegal.dto.LoginDTO;
import com.smartlegal.dto.RegisterDTO;
import com.smartlegal.service.AuthService;
import com.smartlegal.vo.LoginVO;
import com.smartlegal.vo.UserVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

/**
 * 认证控制器
 */
@Slf4j
@RestController
@RequestMapping("/api/v1/auth")
@RequiredArgsConstructor
@Tag(name = "认证管理", description = "登录、注册、令牌刷新")
public class AuthController {

    private final AuthService authService;

    @PostMapping("/login")
    @Operation(summary = "用户登录")
    public Result<LoginVO> login(@Valid @RequestBody LoginDTO loginDTO) {
        LoginVO loginVO = authService.login(loginDTO);
        return Result.success("登录成功", loginVO);
    }

    @PostMapping("/register")
    @Operation(summary = "用户注册")
    public Result<UserVO> register(@Valid @RequestBody RegisterDTO registerDTO) {
        UserVO userVO = authService.register(registerDTO);
        return Result.success("注册成功", userVO);
    }

    @PostMapping("/refresh")
    @Operation(summary = "刷新令牌")
    public Result<LoginVO> refresh(@RequestParam String refreshToken) {
        LoginVO loginVO = authService.refresh(refreshToken);
        return Result.success(loginVO);
    }

    @GetMapping("/me")
    @Operation(summary = "获取当前用户信息")
    public Result<UserVO> getCurrentUser() {
        UserVO userVO = authService.getCurrentUser();
        return Result.success(userVO);
    }
}
