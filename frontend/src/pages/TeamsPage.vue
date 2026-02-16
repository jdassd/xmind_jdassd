<template>
  <div class="teams-page">
    <div class="page-header">
      <h1>Teams</h1>
      <p class="page-desc">Manage your teams and collaborate with others</p>
    </div>

    <div v-if="invitations.length > 0" class="section">
      <div class="section-header">
        <h2>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
          Pending Invitations
        </h2>
        <span class="count pulse">{{ invitations.length }}</span>
      </div>
      <div class="invite-list">
        <div v-for="inv in invitations" :key="inv.id" class="invite-item">
          <div class="invite-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
          </div>
          <div class="invite-info">
            <strong>{{ inv.team_name }}</strong>
            <span class="invite-meta">Invited by {{ inv.inviter_name }} as <span class="role-highlight">{{ inv.role }}</span></span>
          </div>
          <div class="invite-actions">
            <button class="btn-accept" @click="accept(inv.id)">Accept</button>
            <button class="btn-decline" @click="decline(inv.id)">Decline</button>
          </div>
        </div>
      </div>
    </div>

    <div class="section">
      <div class="section-header">
        <h2>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
          My Teams
        </h2>
        <span class="count">{{ teams.length }}</span>
      </div>
      <div class="team-list">
        <div v-for="t in teams" :key="t.id" class="team-item" @click="router.push(`/teams/${t.id}`)">
          <div class="team-avatar">{{ t.name.slice(0, 2).toUpperCase() }}</div>
          <div class="team-info">
            <span class="team-name">{{ t.name }}</span>
            <span class="badge" :class="t.role">{{ t.role }}</span>
          </div>
          <button v-if="t.role === 'owner'" class="btn-delete" @click.stop="removeTeam(t.id)" title="Delete team">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
          </button>
          <svg class="chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
        </div>
        <div v-if="teams.length === 0" class="empty-state">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" opacity="0.3"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
          <p>No teams yet. Create one to start collaborating.</p>
        </div>
      </div>
    </div>

    <div class="create-section">
      <div class="create-form">
        <div class="create-input-group">
          <svg class="create-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          <input v-model="newTeamName" placeholder="Create a new team..." @keyup.enter="createTeam" />
        </div>
        <button class="btn-create" @click="createTeam">
          Create Team
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTeamsStore } from '../stores/teams'
import { storeToRefs } from 'pinia'

const router = useRouter()
const teamsStore = useTeamsStore()
const { teams, invitations } = storeToRefs(teamsStore)
const newTeamName = ref('')

async function createTeam() {
  const name = newTeamName.value.trim()
  if (!name) return
  await teamsStore.createTeam(name)
  newTeamName.value = ''
}

async function removeTeam(id: string) {
  await teamsStore.deleteTeam(id)
}

async function accept(id: string) {
  await teamsStore.acceptInvitation(id)
}

async function decline(id: string) {
  await teamsStore.declineInvitation(id)
}

onMounted(() => {
  teamsStore.fetchTeams()
  teamsStore.fetchInvitations()
})
</script>

<style scoped>
.teams-page {
  max-width: 680px;
  margin: 0 auto;
  padding: 48px 24px;
  animation: pageIn 0.4s var(--ease-out) both;
}

@keyframes pageIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.page-header {
  margin-bottom: 40px;
}

.page-header h1 {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.03em;
  margin-bottom: 6px;
}

.page-desc {
  font-size: 14px;
  color: var(--text-tertiary);
}

.section {
  margin-bottom: 36px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}

.section-header h2 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.count {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-tertiary);
  background: var(--bg-elevated);
  padding: 2px 8px;
  border-radius: 10px;
}

.count.pulse {
  background: var(--color-warning-bg);
  color: var(--color-warning);
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.invite-list, .team-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.invite-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  background: var(--color-warning-bg);
  border: 1px solid rgba(251, 191, 36, 0.12);
  border-radius: var(--radius-md);
}

.invite-icon {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  background: rgba(251, 191, 36, 0.1);
  color: var(--color-warning);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.invite-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.invite-info strong {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.invite-meta {
  font-size: 12px;
  color: var(--text-tertiary);
}

.role-highlight {
  color: var(--accent);
  font-weight: 500;
}

.invite-actions {
  display: flex;
  gap: 6px;
}

.btn-accept {
  padding: 6px 16px;
  background: var(--accent-green);
  color: var(--text-inverse);
  border: none;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
}

.btn-accept:hover {
  filter: brightness(1.1);
  transform: translateY(-1px);
}

.btn-decline {
  padding: 6px 14px;
  background: none;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  color: var(--text-secondary);
  transition: all var(--duration-fast) var(--ease-out);
}

.btn-decline:hover {
  border-color: var(--color-error);
  color: var(--color-error);
}

.team-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
}

.team-item:hover {
  background: var(--bg-elevated);
  border-color: var(--border-default);
  transform: translateX(4px);
}

.team-avatar {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  background: linear-gradient(135deg, #818cf8, var(--accent));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  color: var(--text-inverse);
  flex-shrink: 0;
}

.team-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
}

.team-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.badge {
  font-size: 10px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 10px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  background: var(--bg-hover);
  color: var(--text-secondary);
}

.badge.owner {
  background: var(--color-warning-bg);
  color: var(--color-warning);
}

.badge.admin {
  background: var(--accent-glow);
  color: var(--accent);
}

.badge.editor {
  background: var(--accent-green-glow);
  color: var(--accent-green);
}

.chevron {
  color: var(--text-tertiary);
  flex-shrink: 0;
  opacity: 0;
  transition: opacity var(--duration-fast);
}

.team-item:hover .chevron {
  opacity: 1;
}

.btn-delete {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: none;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: all var(--duration-fast) var(--ease-out);
  opacity: 0;
}

.team-item:hover .btn-delete {
  opacity: 1;
}

.btn-delete:hover {
  color: var(--color-error);
  background: var(--color-error-bg);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 40px 20px;
  color: var(--text-tertiary);
  font-size: 13px;
}

.create-section {
  margin-top: 8px;
  padding-top: 24px;
  border-top: 1px solid var(--border-subtle);
}

.create-form {
  display: flex;
  gap: 8px;
}

.create-input-group {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 14px;
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  transition: all var(--duration-fast) var(--ease-out);
}

.create-icon {
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.create-input-group:focus-within {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-glow);
}

.create-input-group:focus-within .create-icon {
  color: var(--accent);
}

.create-input-group input {
  flex: 1;
  padding: 11px 0;
  background: none;
  border: none;
  font-size: 14px;
  font-family: var(--font-body);
  color: var(--text-primary);
  outline: none;
}

.create-input-group input::placeholder {
  color: var(--text-tertiary);
}

.btn-create {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  background: linear-gradient(135deg, var(--accent), #818cf8);
  color: var(--text-inverse);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  font-family: var(--font-body);
  transition: all var(--duration-fast) var(--ease-out);
  white-space: nowrap;
}

.btn-create:hover {
  box-shadow: var(--shadow-glow);
  transform: translateY(-1px);
}

.btn-create:active {
  transform: translateY(0);
}
</style>
