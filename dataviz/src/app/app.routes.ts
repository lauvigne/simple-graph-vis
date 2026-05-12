import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: 'dashboard',
    loadComponent: () => import('./components/dashboard/dashboard').then((module) => module.Dashboard),
  },
  {
    path: 'treemap',
    loadComponent: () => import('./components/treemap-demo/treemap-demo').then((module) => module.TreemapDemo),
  },
  {
    path: 'sunburst',
    loadComponent: () => import('./components/sunburst-demo/sunburst-demo').then((module) => module.SunburstDemo),
  },
  {
    path: 'capabilities',
    loadComponent: () => import('./components/business-capability-table/business-capability-table').then((module) => module.BusinessCapabilityTable),
  },
  {
    path: 'load-json',
    loadComponent: () => import('./components/json-loader/json-loader').then((module) => module.JsonLoader),
  },
  {
    path: '',
    pathMatch: 'full',
    redirectTo: 'dashboard',
  },
];
