package com.smartlegal.security.annotation;

import java.lang.annotation.*;

/**
 * 自定义权限注解，用于方法级别的权限控制。
 * 标注在Controller方法上，配合SecurityConfig的@EnableMethodSecurity使用。
 *
 * <pre>
 * @RequirePermission("contract:delete")
 * public Result<Void> deleteContract(@PathVariable Long id) { ... }
 * </pre>
 */
@Target({ElementType.METHOD, ElementType.TYPE})
@Retention(RetentionPolicy.RUNTIME)
@Documented
public @interface RequirePermission {

    /**
     * 所需的权限编码，如 "contract:delete"、"review:view" 等
     */
    String value();

    /**
     * 是否必须拥有所有指定的权限
     * true - 逻辑AND（默认），false - 逻辑OR
     */
    boolean requireAll() default true;

    /**
     * 多个权限编码时使用，与value互斥
     */
    String[] permissions() default {};
}
