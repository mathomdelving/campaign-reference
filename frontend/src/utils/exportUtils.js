import { formatCurrency } from './formatters';

export function exportToCSV(data, metrics, filters) {
  // Build CSV header based on enabled metrics
  const headers = ['Candidate Name', 'Candidate ID', 'Party', 'State', 'Office'];
  
  // Add District column for House races
  if (filters.chamber === 'H' || filters.chamber === 'both') {
    headers.push('District');
  }
  
  if (metrics.totalRaised) headers.push('Total Raised');
  if (metrics.totalDisbursed) headers.push('Total Disbursed');
  if (metrics.cashOnHand) headers.push('Cash on Hand');
  
  // Build CSV rows
  const rows = data.map(candidate => {
    const row = [
      candidate.name,
      candidate.candidate_id,
      candidate.party,
      candidate.state,
      candidate.office === 'H' ? 'House' : 'Senate'
    ];
    
    if (filters.chamber === 'H' || filters.chamber === 'both') {
      row.push(candidate.office === 'H' ? candidate.district || '' : '');
    }
    
    if (metrics.totalRaised) row.push(candidate.totalReceipts || 0);
    if (metrics.totalDisbursed) row.push(candidate.totalDisbursements || 0);
    if (metrics.cashOnHand) row.push(candidate.cashOnHand || 0);
    
    return row;
  });
  
  // Combine headers and rows
  const csvContent = [
    headers.join(','),
    ...rows.map(row => row.map(cell => {
      // Escape cells that contain commas or quotes
      if (typeof cell === 'string' && (cell.includes(',') || cell.includes('"'))) {
        return `"${cell.replace(/"/g, '""')}"`;
      }
      return cell;
    }).join(','))
  ].join('\n');
  
  // Create download
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  
  const timestamp = new Date().toISOString().split('T')[0];
  const filename = `fec-dashboard-${filters.cycle}-${timestamp}.csv`;
  
  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

export async function exportChartToPNG(chartRef, filters) {
  try {
    // Use html2canvas library to capture the chart
    const html2canvas = (await import('html2canvas')).default;
    
    if (!chartRef.current) {
      throw new Error('Chart reference not found');
    }
    
    // Create canvas from the chart element
    const canvas = await html2canvas(chartRef.current, {
      backgroundColor: '#ffffff',
      scale: 2, // Higher quality
      logging: false,
      useCORS: true
    });
    
    // Convert to PNG and download
    canvas.toBlob((blob) => {
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);
      
      const timestamp = new Date().toISOString().split('T')[0];
      const filename = `fec-dashboard-chart-${filters.cycle}-${timestamp}.png`;
      
      link.setAttribute('href', url);
      link.setAttribute('download', filename);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    }, 'image/png');
    
  } catch (error) {
    console.error('Error exporting chart:', error);
    alert('Failed to export chart. Please try again.');
  }
}

export function exportTableToPNG(tableRef, filters) {
  return exportChartToPNG(tableRef, filters);
}