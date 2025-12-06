/**
 * Client-side PDF Generation Utility
 * Uses jsPDF and jsPDF-AutoTable for report export
 */
import jsPDF from 'jspdf'
import autoTable from 'jspdf-autotable'

interface SavedReport {
  id: number
  report_name: string | null
  report_type: string
  report_content: any
  profile_snapshot: any
  config_snapshot: any
  overall_confidence: number
  execution_time: number
  total_tokens: number
  created_at: string
}

export const generateReportPDF = (report: SavedReport) => {
  const doc = new jsPDF()
  const pageWidth = doc.internal.pageSize.getWidth()
  const pageHeight = doc.internal.pageSize.getHeight()
  const margin = 20
  let yPosition = margin

  // Helper function to add new page if needed
  const checkPageBreak = (requiredHeight: number) => {
    if (yPosition + requiredHeight > pageHeight - margin) {
      doc.addPage()
      yPosition = margin
    }
  }

  // Helper function to add text with word wrap
  const addText = (text: string, fontSize: number = 12, isBold: boolean = false) => {
    doc.setFontSize(fontSize)
    doc.setFont('helvetica', isBold ? 'bold' : 'normal')
    const lines = doc.splitTextToSize(text, pageWidth - 2 * margin)
    checkPageBreak(lines.length * fontSize * 0.5)
    doc.text(lines, margin, yPosition)
    yPosition += lines.length * fontSize * 0.5 + 5
  }

  // Title
  doc.setFillColor(30, 64, 175) // #1e40af
  doc.rect(0, 0, pageWidth, 40, 'F')
  doc.setTextColor(255, 255, 255)
  doc.setFontSize(24)
  doc.setFont('helvetica', 'bold')
  doc.text('Energy Portfolio Report', pageWidth / 2, 25, { align: 'center' })
  yPosition = 50

  // Reset text color
  doc.setTextColor(0, 0, 0)

  // Report Metadata
  doc.setFontSize(10)
  doc.setFont('helvetica', 'normal')
  const metadata = [
    ['Company:', report.profile_snapshot?.company || 'N/A'],
    ['Industry:', report.profile_snapshot?.industry || 'N/A'],
    ['Location:', report.profile_snapshot?.location || 'N/A'],
    ['Generated:', new Date(report.created_at).toLocaleString()],
    ['Overall Confidence:', `${(report.overall_confidence * 100).toFixed(1)}%`],
    ['Execution Time:', `${report.execution_time.toFixed(1)}s`]
  ]

  autoTable(doc, {
    startY: yPosition,
    head: [],
    body: metadata,
    theme: 'plain',
    styles: { fontSize: 10, cellPadding: 3 },
    columnStyles: {
      0: { fontStyle: 'bold', cellWidth: 50 },
      1: { cellWidth: 120 }
    }
  })

  yPosition = (doc as any).lastAutoTable.finalY + 15

  // Executive Summary
  checkPageBreak(30)
  doc.setFontSize(16)
  doc.setFont('helvetica', 'bold')
  doc.setTextColor(30, 64, 175)
  doc.text('Executive Summary', margin, yPosition)
  yPosition += 10
  doc.setTextColor(0, 0, 0)
  doc.setFontSize(10)
  doc.setFont('helvetica', 'normal')

  const portfolioAgent = report.report_content?.portfolio_agent || {}
  const portfolio = portfolioAgent.portfolio || {}
  const esgScores = portfolio.esg_scores || {}
  const renewablePct = esgScores.renewable_percentage || 0
  const targetPct = report.profile_snapshot?.sustainability_target_kp2 || 0
  const meetsTarget = portfolio.meets_targets || false

  const summaryText = `This report presents a comprehensive energy portfolio recommendation for ${
    report.profile_snapshot?.industry || 'your industry'
  } operations in ${report.profile_snapshot?.location || 'your location'}.

Key Findings:
• Recommended renewable energy mix: ${renewablePct.toFixed(1)}%
• Sustainability target: ${targetPct.toFixed(1)}% renewable by ${
    report.profile_snapshot?.sustainability_target_kp1 || 2030
  }
• Target status: ${meetsTarget ? 'Target Achieved' : 'In Progress'}
• Budget alignment: ₹${(report.profile_snapshot?.budget || 0).toLocaleString()} annual budget`

  addText(summaryText, 10)

  // Energy Mix Section
  checkPageBreak(40)
  doc.setFontSize(16)
  doc.setFont('helvetica', 'bold')
  doc.setTextColor(30, 64, 175)
  doc.text('Recommended Energy Mix', margin, yPosition)
  yPosition += 10
  doc.setTextColor(0, 0, 0)

  const optimizationAgent = report.report_content?.optimization_agent || {}
  const optimizedMix = optimizationAgent.optimized_mix || []

  if (optimizedMix.length > 0) {
    const energyMixData = optimizedMix.map((item: any) => [
      item.source || 'Unknown',
      `${(item.percentage || 0).toFixed(1)}%`,
      `${(item.annual_energy_kwh || 0).toLocaleString()} kWh`,
      `₹${(item.annual_cost_inr || 0).toLocaleString()}`
    ])

    // Add totals
    const totalPct = optimizedMix.reduce((sum: number, item: any) => sum + (item.percentage || 0), 0)
    const totalEnergy = optimizedMix.reduce((sum: number, item: any) => sum + (item.annual_energy_kwh || 0), 0)
    const totalCost = optimizedMix.reduce((sum: number, item: any) => sum + (item.annual_cost_inr || 0), 0)

    energyMixData.push([
      'Total',
      `${totalPct.toFixed(1)}%`,
      `${totalEnergy.toLocaleString()} kWh`,
      `₹${totalCost.toLocaleString()}`
    ])

    autoTable(doc, {
      startY: yPosition,
      head: [['Energy Source', 'Percentage', 'Annual kWh', 'Annual Cost (₹)']],
      body: energyMixData,
      theme: 'striped',
      headStyles: { fillColor: [30, 64, 175], textColor: 255 },
      styles: { fontSize: 9, cellPadding: 4 },
      columnStyles: {
        0: { cellWidth: 40 },
        1: { cellWidth: 30, halign: 'center' },
        2: { cellWidth: 50, halign: 'right' },
        3: { cellWidth: 50, halign: 'right' }
      },
      footStyles: { fontStyle: 'bold', fillColor: [226, 232, 240] }
    })

    yPosition = (doc as any).lastAutoTable.finalY + 15
  }

  // ESG Assessment
  checkPageBreak(40)
  doc.setFontSize(16)
  doc.setFont('helvetica', 'bold')
  doc.setTextColor(30, 64, 175)
  doc.text('ESG & Sustainability Assessment', margin, yPosition)
  yPosition += 10
  doc.setTextColor(0, 0, 0)

  const esgData = [
    ['Renewable Percentage', `${(esgScores.renewable_percentage || 0).toFixed(1)}%`, meetsTarget ? '✓ Achieved' : '○ In Progress'],
    ['Carbon Reduction', `${(esgScores.carbon_reduction_estimate || 0).toFixed(1)}%`, '✓'],
    ['Sustainability Score', `${(esgScores.overall_sustainability_score || 0).toFixed(2)}/1.00`,
     esgScores.overall_sustainability_score >= 0.8 ? '✓ Excellent' : esgScores.overall_sustainability_score >= 0.6 ? '○ Good' : '○ Fair'],
    ['Target Achievement', meetsTarget ? 'Yes' : 'In Progress', meetsTarget ? '✓' : '○']
  ]

  autoTable(doc, {
    startY: yPosition,
    head: [['Metric', 'Value', 'Status']],
    body: esgData,
    theme: 'striped',
    headStyles: { fillColor: [16, 185, 129], textColor: 255 },
    styles: { fontSize: 9, cellPadding: 4 }
  })

  yPosition = (doc as any).lastAutoTable.finalY + 15

  // Transition Roadmap
  checkPageBreak(40)
  doc.setFontSize(16)
  doc.setFont('helvetica', 'bold')
  doc.setTextColor(30, 64, 175)
  doc.text('Transition Roadmap', margin, yPosition)
  yPosition += 10
  doc.setTextColor(0, 0, 0)

  const roadmap = portfolio.transition_roadmap || []

  if (roadmap.length > 0) {
    const roadmapData = roadmap.map((item: any) => [
      item.year?.toString() || '',
      `${(item.renewable_percentage || 0).toFixed(1)}%`,
      item.milestone || ''
    ])

    autoTable(doc, {
      startY: yPosition,
      head: [['Year', 'Renewable %', 'Milestone']],
      body: roadmapData,
      theme: 'striped',
      headStyles: { fillColor: [30, 64, 175], textColor: 255 },
      styles: { fontSize: 9, cellPadding: 4 },
      columnStyles: {
        0: { cellWidth: 25, halign: 'center' },
        1: { cellWidth: 30, halign: 'center' },
        2: { cellWidth: 115 }
      }
    })

    yPosition = (doc as any).lastAutoTable.finalY + 15
  }

  // New page for detailed analysis
  doc.addPage()
  yPosition = margin

  // Detailed Analysis
  doc.setFontSize(16)
  doc.setFont('helvetica', 'bold')
  doc.setTextColor(30, 64, 175)
  doc.text('Detailed Analysis', margin, yPosition)
  yPosition += 15
  doc.setTextColor(0, 0, 0)

  // Energy Availability Analysis
  const availabilityAgent = report.report_content?.availability_agent || {}
  if (availabilityAgent.reasoning) {
    doc.setFontSize(14)
    doc.setFont('helvetica', 'bold')
    doc.text('Energy Availability Analysis', margin, yPosition)
    yPosition += 8

    const confidence = availabilityAgent.confidence || 0
    doc.setFontSize(10)
    doc.setFont('helvetica', 'bold')
    doc.setTextColor(confidence >= 0.7 ? 16 : confidence >= 0.4 ? 245 : 239,
                     confidence >= 0.7 ? 185 : confidence >= 0.4 ? 158 : 68,
                     confidence >= 0.7 ? 129 : confidence >= 0.4 ? 11 : 68)
    doc.text(`Confidence: ${(confidence * 100).toFixed(1)}%`, margin, yPosition)
    yPosition += 8

    doc.setTextColor(0, 0, 0)
    doc.setFont('helvetica', 'normal')
    addText(availabilityAgent.reasoning.substring(0, 800), 9)
  }

  // Price Optimization Analysis
  if (optimizationAgent.reasoning) {
    checkPageBreak(30)
    doc.setFontSize(14)
    doc.setFont('helvetica', 'bold')
    doc.text('Price Optimization Analysis', margin, yPosition)
    yPosition += 8

    const confidence = optimizationAgent.confidence || 0
    doc.setFontSize(10)
    doc.setFont('helvetica', 'bold')
    doc.setTextColor(confidence >= 0.7 ? 16 : confidence >= 0.4 ? 245 : 239,
                     confidence >= 0.7 ? 185 : confidence >= 0.4 ? 158 : 68,
                     confidence >= 0.7 ? 129 : confidence >= 0.4 ? 11 : 68)
    doc.text(`Confidence: ${(confidence * 100).toFixed(1)}%`, margin, yPosition)
    yPosition += 8

    doc.setTextColor(0, 0, 0)
    doc.setFont('helvetica', 'normal')
    addText(optimizationAgent.reasoning.substring(0, 800), 9)
  }

  // Portfolio Decision Analysis
  if (portfolioAgent.reasoning) {
    checkPageBreak(30)
    doc.setFontSize(14)
    doc.setFont('helvetica', 'bold')
    doc.text('Portfolio Decision Analysis', margin, yPosition)
    yPosition += 8

    const confidence = portfolioAgent.confidence || 0
    doc.setFontSize(10)
    doc.setFont('helvetica', 'bold')
    doc.setTextColor(confidence >= 0.7 ? 16 : confidence >= 0.4 ? 245 : 239,
                     confidence >= 0.7 ? 185 : confidence >= 0.4 ? 158 : 68,
                     confidence >= 0.7 ? 129 : confidence >= 0.4 ? 11 : 68)
    doc.text(`Confidence: ${(confidence * 100).toFixed(1)}%`, margin, yPosition)
    yPosition += 8

    doc.setTextColor(0, 0, 0)
    doc.setFont('helvetica', 'normal')
    addText(portfolioAgent.reasoning.substring(0, 800), 9)
  }

  // Generate filename
  const timestamp = new Date(report.created_at).toISOString().split('T')[0]
  const filename = `energy_report_${timestamp}.pdf`

  // Save PDF
  doc.save(filename)
}
