/**
 * Form validation rules for Element Plus el-form components.
 *
 * Each exported constant is an array of `FormItemRule` objects that can be
 * spread directly into the `rules` prop of an `<el-form-item>`.
 *
 * All validation error messages are in Chinese.
 */

import type { FormItemRule } from 'element-plus'

// ---------------------------------------------------------------------------
// 1. Username Rules
// ---------------------------------------------------------------------------

/**
 * Validation rules for username fields.
 *
 * - Required
 * - 2–20 characters
 * - Only Chinese characters, English letters, digits, and underscores
 */
export const usernameRules: FormItemRule[] = [
  {
    required: true,
    message: '请输入用户名',
    trigger: 'blur',
  },
  {
    min: 2,
    max: 20,
    message: '用户名长度为 2 ~ 20 个字符',
    trigger: 'blur',
  },
  {
    pattern: /^[一-龥a-zA-Z0-9_]+$/,
    message: '用户名只能包含中文、字母、数字和下划线',
    trigger: 'blur',
  },
]

// ---------------------------------------------------------------------------
// 2. Password Rules
// ---------------------------------------------------------------------------

/**
 * Validation rules for password fields.
 *
 * - Required
 * - 6–20 characters
 */
export const passwordRules: FormItemRule[] = [
  {
    required: true,
    message: '请输入密码',
    trigger: 'blur',
  },
  {
    min: 6,
    max: 20,
    message: '密码长度为 6 ~ 20 个字符',
    trigger: 'blur',
  },
]

/**
 * Stronger password rules (requires mix of character types).
 */
export const strongPasswordRules: FormItemRule[] = [
  ...passwordRules,
  {
    pattern: /^(?=.*[a-zA-Z])(?=.*\d).{6,20}$/,
    message: '密码必须包含字母和数字',
    trigger: 'blur',
  },
]

// ---------------------------------------------------------------------------
// 3. Confirm Password Rules
// ---------------------------------------------------------------------------

/**
 * Creates rules for confirming a password match against another form field.
 *
 * @param passwordFieldRef - A function that returns the current value of the
 *   password field being confirmed (e.g. `() => form.password`).
 */
export function createConfirmPasswordRules(
  passwordFieldRef: () => string,
): FormItemRule[] {
  return [
    {
      required: true,
      message: '请再次输入密码',
      trigger: 'blur',
    },
    {
      validator: (_rule, value, callback) => {
        if (value !== passwordFieldRef()) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ]
}

// ---------------------------------------------------------------------------
// 4. Email Rules
// ---------------------------------------------------------------------------

/**
 * Validation rules for email fields.
 */
export const emailRules: FormItemRule[] = [
  {
    type: 'email',
    message: '请输入有效的邮箱地址',
    trigger: ['blur', 'change'],
  },
]

/**
 * Required email rules.
 */
export const requiredEmailRules: FormItemRule[] = [
  {
    required: true,
    message: '请输入邮箱地址',
    trigger: 'blur',
  },
  ...emailRules,
]

// ---------------------------------------------------------------------------
// 5. Phone Rules
// ---------------------------------------------------------------------------

/**
 * Validation rules for Chinese mobile phone numbers.
 */
export const phoneRules: FormItemRule[] = [
  {
    pattern: /^1[3-9]\d{9}$/,
    message: '请输入有效的手机号码',
    trigger: ['blur', 'change'],
  },
]

/**
 * Required phone number rules.
 */
export const requiredPhoneRules: FormItemRule[] = [
  {
    required: true,
    message: '请输入手机号码',
    trigger: 'blur',
  },
  ...phoneRules,
]

// ---------------------------------------------------------------------------
// 6. URL Rules
// ---------------------------------------------------------------------------

/**
 * Validation rules for URL fields.
 */
export const urlRules: FormItemRule[] = [
  {
    type: 'url',
    message: '请输入有效的链接地址',
    trigger: ['blur', 'change'],
  },
]

// ---------------------------------------------------------------------------
// 7. ID Number Rules (Chinese ID card)
// ---------------------------------------------------------------------------

/**
 * Validation rules for Chinese 18-digit ID card numbers.
 */
export const idCardRules: FormItemRule[] = [
  {
    required: true,
    message: '请输入身份证号码',
    trigger: 'blur',
  },
  {
    pattern: /^[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]$/,
    message: '请输入有效的身份证号码',
    trigger: ['blur', 'change'],
  },
]

// ---------------------------------------------------------------------------
// 8. Generic Required Rule Factory
// ---------------------------------------------------------------------------

/**
 * Creates a required-field validation rule with a Chinese label.
 *
 * Usage:
 *   <el-form-item label="合同名称" :rules="[requiredRule('合同名称')]">
 *
 * @param fieldName - The display name of the field (used in the error message).
 * @param trigger   - When to trigger validation (default: 'blur').
 */
export function requiredRule(
  fieldName: string,
  trigger: 'blur' | 'change' = 'blur',
): FormItemRule {
  return {
    required: true,
    message: `请输入${fieldName}`,
    trigger,
  }
}

/**
 * Creates a required selector rule (for selects, cascaders, etc.).
 *
 * @param fieldName - The display name of the field.
 * @param trigger   - Trigger event (default: 'change').
 */
export function requiredSelectRule(
  fieldName: string,
  trigger: 'blur' | 'change' = 'change',
): FormItemRule {
  return {
    required: true,
    message: `请选择${fieldName}`,
    trigger,
  }
}

// ---------------------------------------------------------------------------
// 9. Length-constrained Rules
// ---------------------------------------------------------------------------

/**
 * Creates min/max length rules.
 *
 * @param min - Minimum character count.
 * @param max - Maximum character count.
 */
export function lengthRule(min: number, max: number): FormItemRule {
  return {
    min,
    max,
    message: `长度在 ${min} 到 ${max} 个字符之间`,
    trigger: 'blur',
  }
}

// ---------------------------------------------------------------------------
// 10. Numeric Rules
// ---------------------------------------------------------------------------

/**
 * Rules for positive integer fields.
 */
export const positiveIntegerRules: FormItemRule[] = [
  {
    required: true,
    message: '请输入数量',
    trigger: 'blur',
  },
  {
    type: 'integer',
    message: '请输入整数',
    trigger: 'blur',
  },
  {
    validator: (_rule, value, callback) => {
      if (Number(value) <= 0) {
        callback(new Error('请输入大于0的数字'))
      } else {
        callback()
      }
    },
    trigger: 'blur',
  },
]

/**
 * Rules for optional numeric fields (allows empty).
 */
export const optionalNumberRule: FormItemRule = {
  type: 'number',
  message: '请输入有效的数字',
  trigger: ['blur', 'change'],
}

// ---------------------------------------------------------------------------
// 11. Date Rules
// ---------------------------------------------------------------------------

/**
 * Required date picker rule.
 *
 * @param fieldName - Field display name.
 */
export function requiredDateRule(fieldName: string): FormItemRule {
  return {
    type: 'date',
    required: true,
    message: `请选择${fieldName}`,
    trigger: 'change',
  }
}

// ---------------------------------------------------------------------------
// 12. File Upload Rules
// ---------------------------------------------------------------------------

/**
 * Creates rules for file upload fields that accept specific file types.
 *
 * @param extensions - Allowed file extensions, e.g. ['.pdf', '.docx'].
 * @param maxSizeMB  - Maximum file size in megabytes.
 */
export function createFileUploadRules(
  extensions: string[] = [],
  maxSizeMB: number = 10,
): FormItemRule[] {
  const rules: FormItemRule[] = [
    {
      required: true,
      message: '请上传文件',
      trigger: 'change',
    },
  ]

  if (extensions.length > 0) {
    const extList = extensions.join('、')
    rules.push({
      validator: (_rule, value: File | File[], callback) => {
        if (!value) {
          callback()
          return
        }
        const files = Array.isArray(value) ? value : [value]
        for (const file of files) {
          const suffix = file.name
            .substring(file.name.lastIndexOf('.'))
            .toLowerCase()
          if (!extensions.includes(suffix)) {
            callback(new Error(`仅支持上传 ${extList} 格式的文件`))
            return
          }
        }
        callback()
      },
      trigger: 'change',
    })
  }

  rules.push({
    validator: (_rule, value: File | File[], callback) => {
      if (!value) {
        callback()
        return
      }
      const files = Array.isArray(value) ? value : [value]
      const maxBytes = maxSizeMB * 1024 * 1024
      for (const file of files) {
        if (file.size > maxBytes) {
          callback(new Error(`文件大小不能超过 ${maxSizeMB}MB`))
          return
        }
      }
      callback()
    },
    trigger: 'change',
  })

  return rules
}

// ---------------------------------------------------------------------------
// 13. Convenience aggregate rule sets
// ---------------------------------------------------------------------------

/**
 * Login form rules (username + password).
 */
export const loginFormRules: Record<string, FormItemRule[]> = {
  username: [requiredRule('用户名')],
  password: [requiredRule('密码')],
}

/**
 * User form rules for creating/editing users.
 */
export const userFormRules: Record<string, FormItemRule[]> = {
  username: usernameRules,
  password: passwordRules,
  email: requiredEmailRules,
  phone: phoneRules,
}

/**
 * Contract basic info rules.
 */
export const contractFormRules: Record<string, FormItemRule[]> = {
  title: [requiredRule('合同名称'), lengthRule(2, 100)],
  partyA: [requiredRule('甲方')],
  partyB: [requiredRule('乙方')],
  signDate: [requiredDateRule('签约日期')],
}
