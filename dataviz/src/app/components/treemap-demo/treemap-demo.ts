import { Component } from '@angular/core';
import { TreemapData } from '../../models/treemap-data';
import { BusinessDomainTreemap } from '../business-domain-treemap/business-domain-treemap';

@Component({
  selector: 'app-treemap-demo',
  imports: [BusinessDomainTreemap],
  templateUrl: './treemap-demo.html',
  styleUrl: './treemap-demo.scss',
})
export class TreemapDemo {
  readonly applicationCountData: TreemapData = {
    label: 'Business domains - applications',
    metric: {
      key: 'applicationCount',
      label: 'Applications',
    },
    children: [
      {
        id: 'retail-banking',
        label: 'Retail Banking',
        children: [
          { id: 'retail-payments', label: 'Payments', value: 58 },
          { id: 'retail-lending', label: 'Lending', value: 44 },
          { id: 'customer-servicing', label: 'Customer Servicing', value: 39 },
          { id: 'cards-wallets', label: 'Cards & Wallets', value: 31 },
        ],
      },
      {
        id: 'wealth-management',
        label: 'Wealth Management',
        children: [
          { id: 'portfolio-management', label: 'Portfolio Management', value: 35 },
          { id: 'advisory', label: 'Advisory', value: 24 },
          { id: 'client-reporting', label: 'Client Reporting', value: 19 },
        ],
      },
      {
        id: 'corporate-banking',
        label: 'Corporate Banking',
        children: [
          { id: 'cash-management', label: 'Cash Management', value: 47 },
          { id: 'trade-finance', label: 'Trade Finance', value: 29 },
          { id: 'corporate-lending', label: 'Corporate Lending', value: 41 },
          { id: 'treasury-services', label: 'Treasury Services', value: 22 },
        ],
      },
      {
        id: 'risk-compliance',
        label: 'Risk & Compliance',
        children: [
          { id: 'aml-kyc', label: 'AML / KYC', value: 33 },
          { id: 'fraud', label: 'Fraud', value: 18 },
          { id: 'regulatory-reporting', label: 'Regulatory Reporting', value: 27 },
        ],
      },
      {
        id: 'enterprise-enabling',
        label: 'Enterprise Enabling',
        children: [
          { id: 'identity-access', label: 'Identity & Access', value: 26 },
          { id: 'master-data', label: 'Master Data', value: 21 },
          { id: 'integration', label: 'Integration', value: 38 },
          { id: 'operations', label: 'Operations', value: 34 },
        ],
      },
    ],
  };

  readonly tcoData: TreemapData = {
    label: 'Business domains - TCO',
    metric: {
      key: 'tco',
      label: 'TCO',
      unit: 'kEUR',
    },
    children: [
      {
        id: 'retail-banking-tco',
        label: 'Retail Banking',
        children: [
          { id: 'retail-payments-tco', label: 'Payments', value: 1380 },
          { id: 'retail-lending-tco', label: 'Lending', value: 1120 },
          { id: 'customer-servicing-tco', label: 'Customer Servicing', value: 860 },
          { id: 'cards-wallets-tco', label: 'Cards & Wallets', value: 740 },
        ],
      },
      {
        id: 'corporate-banking-tco',
        label: 'Corporate Banking',
        children: [
          { id: 'cash-management-tco', label: 'Cash Management', value: 1260 },
          { id: 'trade-finance-tco', label: 'Trade Finance', value: 920 },
          { id: 'corporate-lending-tco', label: 'Corporate Lending', value: 1180 },
        ],
      },
      {
        id: 'risk-compliance-tco',
        label: 'Risk & Compliance',
        children: [
          { id: 'aml-kyc-tco', label: 'AML / KYC', value: 980 },
          { id: 'fraud-tco', label: 'Fraud', value: 640 },
          { id: 'regulatory-reporting-tco', label: 'Regulatory Reporting', value: 790 },
        ],
      },
    ],
  };
}
