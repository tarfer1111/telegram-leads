import api from './api';
import type {
    ProjectResponse,
    ProjectCreate,
    ProjectWithManagersResponse,
    BotResponse,
    BotCreate,
    BotUpdate,
    AddManagersRequest
} from '@/types/api.types';

export async function getProjects(): Promise<ProjectResponse[]> {
    const response = await api.get<ProjectResponse[]>('/admin/projects');
    return response.data;
}

export async function createProject(data: ProjectCreate): Promise<ProjectResponse> {
    const response = await api.post<ProjectResponse>('/admin/projects', data);
    return response.data;
}

export async function getProjectDetails(projectId: number): Promise<ProjectWithManagersResponse> {
    const response = await api.get<ProjectWithManagersResponse>(`/admin/projects/${projectId}`);
    return response.data;
}

export async function updateProject(projectId: number, data: ProjectCreate): Promise<ProjectResponse> {
    const response = await api.put<ProjectResponse>(`/admin/projects/${projectId}`, data);
    return response.data;
}

export async function deleteProject(projectId: number): Promise<void> {
    await api.delete(`/admin/projects/${projectId}`);
}

export async function addManagersToProject(projectId: number, data: AddManagersRequest): Promise<void> {
    await api.post(`/admin/projects/${projectId}/managers`, data);
}

export async function removeManagerFromProject(projectId: number, managerId: number): Promise<void> {
    await api.delete(`/admin/projects/${projectId}/managers/${managerId}`);
}

export async function getProjectBots(projectId: number): Promise<BotResponse[]> {
    const response = await api.get<BotResponse[]>(`/admin/projects/${projectId}/bots`);
    return response.data;
}

export async function createBot(projectId: number, data: BotCreate): Promise<BotResponse> {
    const response = await api.post<BotResponse>(`/admin/projects/${projectId}/bots`, data);
    return response.data;
}

export async function updateBot(projectId: number, botId: number, data: BotUpdate): Promise<BotResponse> {
    const response = await api.put<BotResponse>(`/admin/projects/${projectId}/bots/${botId}`, data);
    return response.data;
}

export async function deleteBot(projectId: number, botId: number): Promise<void> {
    await api.delete(`/admin/projects/${projectId}/bots/${botId}`);
}