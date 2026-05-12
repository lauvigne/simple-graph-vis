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
    path: 'load-json',
    loadComponent: () => import('./components/json-loader/json-loader').then((module) => module.JsonLoader),
  },
  {
    path: '',
    pathMatch: 'full',
    redirectTo: 'dashboard',
  },
];
