import api from './api';
import type {
    ManagerResponse,
    ManagerCreate,
    ManagerUpdate
} from '@/types/api.types';

export async function getManagers(): Promise<ManagerResponse[]> {
    const response = await api.get<ManagerResponse[]>('/admin/managers');
    return response.data;
}

export async function createManager(data: ManagerCreate): Promise<ManagerResponse> {
    const response = await api.post<ManagerResponse>('/admin/managers', data);
    return response.data;
}

export async function updateManager(managerId: number, data: ManagerUpdate): Promise<ManagerResponse> {
    const response = await api.put<ManagerResponse>(`/admin/managers/${managerId}`, data);
    return response.data;
}

export async function deleteManager(managerId: number): Promise<void> {
    await api.delete(`/admin/managers/${managerId}`);
}