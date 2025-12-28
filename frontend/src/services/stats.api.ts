import api from './api';
import type { OverviewStats, ManagerStats, DailyStats } from '@/types/api.types';

export interface ManagerStats24h {
    manager_id: number;
    manager_name: string;
    new_leads: number;
    closed_leads: number;
    messages_count: number;
}

export interface DailyManagerStats {
    date: string;
    manager_id: number;
    manager_name: string;
    new_leads: number;
    closed_leads: number;
    messages_count: number;
}

export interface GetDailyManagerStatsParams {
    days?: number;
    start_date?: string;
    end_date?: string;
    manager_id?: number;
}


export async function getOverviewStats(): Promise<OverviewStats> {
    const response = await api.get<OverviewStats>('/stats/overview');
    return response.data;
}

export async function getAllManagerStats(): Promise<ManagerStats[]> {
    const response = await api.get<ManagerStats[]>('/stats/managers');
    return response.data;
}

export async function get24hManagerStats(): Promise<ManagerStats24h[]> {
    const response = await api.get<ManagerStats24h[]>('/stats/last24hours/managers');
    return response.data;
}

export async function getDailyStats(days: number = 7): Promise<DailyStats[]> {
    const response = await api.get<DailyStats[]>('/stats/daily', {
        params: { days }
    });
    return response.data;
}

export async function getDailyManagerStats(params: GetDailyManagerStatsParams): Promise<DailyManagerStats[]> {
    const response = await api.get<DailyManagerStats[]>('/stats/daily/managers', {
        params: params
    });
    return response.data;
}