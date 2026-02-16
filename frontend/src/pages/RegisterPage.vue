<template>
  <div class="register-page">
    <div class="auth-bg">
      <div class="orb orb-1"></div>
      <div class="orb orb-2"></div>
      <div class="orb orb-3"></div>
      <div class="grid-overlay"></div>
    </div>
    <div class="auth-card">
      <div class="auth-brand">
        <svg class="brand-icon" width="36" height="36" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="3" fill="currentColor"/>
          <circle cx="4" cy="6" r="2" fill="currentColor" opacity="0.6"/>
          <circle cx="20" cy="6" r="2" fill="currentColor" opacity="0.6"/>
          <circle cx="4" cy="18" r="2" fill="currentColor" opacity="0.6"/>
          <circle cx="20" cy="18" r="2" fill="currentColor" opacity="0.6"/>
          <line x1="10" y1="11" x2="5.5" y2="7" stroke="currentColor" stroke-width="1.2" opacity="0.4"/>
          <line x1="14" y1="11" x2="18.5" y2="7" stroke="currentColor" stroke-width="1.2" opacity="0.4"/>
          <line x1="10" y1="13" x2="5.5" y2="17" stroke="currentColor" stroke-width="1.2" opacity="0.4"/>
          <line x1="14" y1="13" x2="18.5" y2="17" stroke="currentColor" stroke-width="1.2" opacity="0.4"/>
        </svg>
        <h1>MindMap</h1>
      </div>
      <p class="auth-subtitle">Create your workspace</p>
      <form @submit.prevent="handleRegister">
        <div class="field">
          <label>Username</label>
          <div class="input-wrap">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            <input v-model="username" type="text" required autocomplete="username" placeholder="Choose a username" />
          </div>
        </div>
        <div class="field">
          <label>Email</label>
          <div class="input-wrap">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
            <input v-model="email" type="email" required autocomplete="email" placeholder="your@email.com" />
          </div>
        </div>
        <div class="field">
          <label>Display Name</label>
          <div class="input-wrap">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
            <input v-model="displayName" type="text" placeholder="Optional" />
          </div>
        </div>
        <div class="field">
          <label>Password</label>
          <div class="input-wrap">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
            <input v-model="password" type="password" required minlength="6" autocomplete="new-password" placeholder="Min 6 characters" />
          </div>
        </div>
        <p v-if="error" class="error">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
          {{ error }}
        </p>
        <button type="submit" :disabled="submitting" class="btn-primary">
          <span v-if="submitting" class="spinner"></span>
          {{ submitting ? 'Creating account...' : 'Create Account' }}
        </button>
      </form>
      <p class="switch">
        Already have an account? <router-link to="/login">Sign in</router-link>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

const username = ref('')
const email = ref('')
const displayName = ref('')
const password = ref('')
const error = ref('')
const submitting = ref(false)

async function handleRegister() {
  error.value = ''
  submitting.value = true
  try {
    await auth.register(username.value, email.value, password.value, displayName.value)
    router.push('/')
  } catch (e: any) {
    error.value = e.message || 'Registration failed'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.register-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: var(--bg-base);
  position: relative;
  overflow: hidden;
}

.auth-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  opacity: 0.4;
}

.orb-1 {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, rgba(129, 140, 248, 0.3), transparent 70%);
  top: -10%;
  left: -5%;
  animation: float1 22s ease-in-out infinite;
}

.orb-2 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(52, 211, 153, 0.25), transparent 70%);
  bottom: -10%;
  right: -5%;
  animation: float2 25s ease-in-out infinite;
}

.orb-3 {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(56, 189, 248, 0.15), transparent 70%);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation: float3 18s ease-in-out infinite;
}

.grid-overlay {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.02) 1px, transparent 1px);
  background-size: 60px 60px;
}

@keyframes float1 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -40px) scale(1.05); }
  66% { transform: translate(-20px, 20px) scale(0.95); }
}

@keyframes float2 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(-40px, 30px) scale(1.08); }
  66% { transform: translate(20px, -20px) scale(0.92); }
}

@keyframes float3 {
  0%, 100% { transform: translate(-50%, -50%) scale(1); }
  50% { transform: translate(-50%, -50%) scale(1.15); }
}

.auth-card {
  position: relative;
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xl);
  padding: 44px 40px;
  width: 420px;
  box-shadow: var(--shadow-lg);
  backdrop-filter: blur(20px);
  animation: cardIn 0.6s var(--ease-out) both;
}

@keyframes cardIn {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.97);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.auth-brand {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 6px;
}

.brand-icon {
  color: var(--accent);
}

.auth-brand h1 {
  font-family: var(--font-display);
  font-size: 26px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.03em;
}

.auth-subtitle {
  text-align: center;
  font-size: 14px;
  color: var(--text-tertiary);
  margin-bottom: 32px;
}

.field {
  margin-bottom: 18px;
}

.field label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.input-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 14px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  transition: all var(--duration-fast) var(--ease-out);
}

.input-wrap svg {
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.input-wrap:focus-within {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-glow);
}

.input-wrap:focus-within svg {
  color: var(--accent);
}

.input-wrap input {
  flex: 1;
  padding: 12px 0;
  background: none;
  border: none;
  font-size: 14px;
  font-family: var(--font-body);
  color: var(--text-primary);
  outline: none;
}

.input-wrap input::placeholder {
  color: var(--text-tertiary);
}

.error {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--color-error);
  font-size: 13px;
  margin: 0 0 16px;
  padding: 10px 14px;
  background: var(--color-error-bg);
  border-radius: var(--radius-sm);
  border: 1px solid rgba(248, 113, 113, 0.15);
}

.btn-primary {
  width: 100%;
  padding: 12px;
  background: linear-gradient(135deg, var(--accent), #818cf8);
  color: var(--text-inverse);
  border: none;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 600;
  font-family: var(--font-body);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all var(--duration-fast) var(--ease-out);
  position: relative;
  overflow: hidden;
}

.btn-primary::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, transparent, rgba(255,255,255,0.1));
  opacity: 0;
  transition: opacity var(--duration-fast);
}

.btn-primary:hover:not(:disabled)::after {
  opacity: 1;
}

.btn-primary:hover:not(:disabled) {
  box-shadow: var(--shadow-glow);
  transform: translateY(-1px);
}

.btn-primary:active:not(:disabled) {
  transform: translateY(0);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: default;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.switch {
  text-align: center;
  margin-top: 24px;
  font-size: 13px;
  color: var(--text-tertiary);
}

.switch a {
  color: var(--accent);
  text-decoration: none;
  font-weight: 500;
  transition: color var(--duration-fast);
}

.switch a:hover {
  color: var(--accent-hover);
}
</style>
