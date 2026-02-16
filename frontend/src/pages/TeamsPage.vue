<template>
  <div class="teams-page">
    <div v-if="invitations.length > 0" class="section">
      <h2>Pending Invitations</h2>
      <div class="invite-list">
        <div v-for="inv in invitations" :key="inv.id" class="invite-item">
          <div class="invite-info">
            <strong>{{ inv.team_name }}</strong>
            <span class="invite-meta">Invited by {{ inv.inviter_name }} as {{ inv.role }}</span>
          </div>
          <div class="invite-actions">
            <button class="btn-accept" @click="accept(inv.id)">Accept</button>
            <button class="btn-decline" @click="decline(inv.id)">Decline</button>
          </div>
        </div>
      </div>
    </div>

    <div class="section">
      <h2>My Teams</h2>
      <div class="team-list">
        <div v-for="t in teams" :key="t.id" class="team-item" @click="router.push(`/teams/${t.id}`)">
          <div class="team-info">
            <span class="team-name">{{ t.name }}</span>
            <span class="badge">{{ t.role }}</span>
          </div>
          <button v-if="t.role === 'owner'" class="btn-delete" @click.stop="removeTeam(t.id)">x</button>
        </div>
      </div>
    </div>

    <div class="create-form">
      <input v-model="newTeamName" placeholder="New team name..." @keyup.enter="createTeam" />
      <button @click="createTeam">Create Team</button>
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
  max-width: 600px;
  margin: 0 auto;
  padding: 40px 20px;
}

.section {
  margin-bottom: 32px;
}

.section h2 {
  font-size: 18px;
  color: #333;
  margin: 0 0 12px;
}

.invite-list, .team-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.invite-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #fff9e6;
  border: 1px solid #ffeeba;
  border-radius: 8px;
}

.invite-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.invite-meta {
  font-size: 12px;
  color: #888;
}

.invite-actions {
  display: flex;
  gap: 6px;
}

.btn-accept {
  padding: 4px 12px;
  background: #28a745;
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
}

.btn-decline {
  padding: 4px 12px;
  background: none;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  color: #666;
}

.team-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f5f5f5;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
}

.team-item:hover {
  background: #e8e8e8;
}

.team-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.team-name {
  font-size: 14px;
  font-weight: 500;
}

.badge {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  background: #e2e3e5;
  color: #383d41;
}

.btn-delete {
  background: none;
  border: none;
  color: #999;
  cursor: pointer;
  font-size: 16px;
  padding: 2px 8px;
}

.btn-delete:hover {
  color: #e44;
}

.create-form {
  display: flex;
  gap: 8px;
}

.create-form input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
}

.create-form input:focus {
  border-color: #4a9eff;
}

.create-form button {
  padding: 10px 20px;
  background: #4a9eff;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.create-form button:hover {
  background: #3a8eef;
}
</style>
