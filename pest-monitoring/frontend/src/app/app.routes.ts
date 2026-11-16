import { Routes } from '@angular/router';

import { authGuard } from './core/auth.guard';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'report' },
  {
    path: 'report',
    title: 'Report a sighting – PestPatrol',
    loadComponent: () => import('./features/report/report-sighting').then((m) => m.ReportSighting),
  },
  {
    path: 'my-reports',
    title: 'My reports – PestPatrol',
    canActivate: [authGuard],
    loadComponent: () => import('./features/my-reports/my-reports').then((m) => m.MyReports),
  },
  {
    path: 'map',
    title: 'Pest activity map – PestPatrol',
    loadComponent: () => import('./features/map/pest-map').then((m) => m.PestMap),
  },
  {
    path: 'login',
    title: 'Sign in – PestPatrol',
    loadComponent: () => import('./features/login/login').then((m) => m.Login),
  },
  { path: '**', redirectTo: 'report' },
];