import 'package:flutter/material.dart';

import '../state/app_controller.dart';

class AuthScreen extends StatefulWidget {
  const AuthScreen({required this.controller, super.key});

  final AppController controller;

  @override
  State<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends State<AuthScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _timeZoneController = TextEditingController(text: 'Asia/Shanghai');
  bool _registering = false;
  bool _obscurePassword = true;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _timeZoneController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!(_formKey.currentState?.validate() ?? false)) {
      return;
    }
    FocusScope.of(context).unfocus();
    if (_registering) {
      await widget.controller.register(
        _emailController.text,
        _passwordController.text,
        timeZone: _timeZoneController.text.trim(),
      );
    } else {
      await widget.controller.login(
        _emailController.text,
        _passwordController.text,
      );
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    body: SafeArea(
      child: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 440),
            child: AnimatedBuilder(
              animation: widget.controller,
              builder: (context, _) => Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: <Widget>[
                    Icon(
                      Icons.notifications_active_outlined,
                      size: 64,
                      color: Theme.of(context).colorScheme.primary,
                    ),
                    const SizedBox(height: 16),
                    Text(
                      '随机提醒器',
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.headlineMedium
                          ?.copyWith(fontWeight: FontWeight.w700),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      _registering ? '创建账号并同步你的提醒' : '登录以同步提醒和今日计划',
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.bodyLarge,
                    ),
                    const SizedBox(height: 32),
                    TextFormField(
                      controller: _emailController,
                      keyboardType: TextInputType.emailAddress,
                      textInputAction: TextInputAction.next,
                      autofillHints: const <String>[AutofillHints.email],
                      decoration: const InputDecoration(
                        labelText: '邮箱',
                        prefixIcon: Icon(Icons.mail_outline),
                      ),
                      validator: (value) {
                        final input = value?.trim() ?? '';
                        return input.contains('@') ? null : '请输入有效邮箱';
                      },
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: _passwordController,
                      obscureText: _obscurePassword,
                      textInputAction: TextInputAction.done,
                      autofillHints: const <String>[AutofillHints.password],
                      onFieldSubmitted: (_) => _submit(),
                      decoration: InputDecoration(
                        labelText: '密码',
                        prefixIcon: const Icon(Icons.lock_outline),
                        suffixIcon: IconButton(
                          onPressed: () => setState(
                            () => _obscurePassword = !_obscurePassword,
                          ),
                          icon: Icon(
                            _obscurePassword
                                ? Icons.visibility_outlined
                                : Icons.visibility_off_outlined,
                          ),
                        ),
                      ),
                      validator: (value) {
                        final minimum = _registering ? 8 : 1;
                        return (value?.length ?? 0) >= minimum
                            ? null
                            : _registering
                            ? '密码至少需要 8 个字符'
                            : '请输入密码';
                      },
                    ),
                    if (_registering) ...<Widget>[
                      const SizedBox(height: 16),
                      TextFormField(
                        controller: _timeZoneController,
                        decoration: const InputDecoration(
                          labelText: 'IANA 时区',
                          helperText: '中国用户保持 Asia/Shanghai 即可',
                          prefixIcon: Icon(Icons.public),
                        ),
                        validator: (value) =>
                            (value?.trim().isEmpty ?? true) ? '请输入时区' : null,
                      ),
                    ],
                    if (widget.controller.errorMessage != null) ...<Widget>[
                      const SizedBox(height: 16),
                      Text(
                        widget.controller.errorMessage!,
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: Theme.of(context).colorScheme.error,
                        ),
                      ),
                    ],
                    const SizedBox(height: 24),
                    FilledButton(
                      onPressed: widget.controller.busy ? null : _submit,
                      child: Padding(
                        padding: const EdgeInsets.symmetric(vertical: 12),
                        child: widget.controller.busy
                            ? const SizedBox.square(
                                dimension: 20,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                ),
                              )
                            : Text(_registering ? '注册并登录' : '登录'),
                      ),
                    ),
                    TextButton(
                      onPressed: widget.controller.busy
                          ? null
                          : () {
                              widget.controller.clearMessages();
                              setState(() => _registering = !_registering);
                            },
                      child: Text(_registering ? '已有账号？直接登录' : '没有账号？创建账号'),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    ),
  );
}
