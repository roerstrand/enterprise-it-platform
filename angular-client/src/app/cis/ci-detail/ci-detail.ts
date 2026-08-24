import { Component, OnInit, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { DatePipe, JsonPipe } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { CIService } from '../ci.service';
import { CIDetail } from '../ci-detail';

@Component({
    selector: 'app-ci-detail',
    imports: [RouterLink, DatePipe, JsonPipe, MatCardModule, MatIconModule, MatProgressSpinnerModule],
    templateUrl: './ci-detail.html',
    styleUrl: './ci-detail.scss',
})
export class CiDetailPage implements OnInit {
    protected readonly ci = signal<CIDetail | null>(null);
    protected readonly loading = signal(true);
    protected readonly notFound = signal(false);

    private ciId!: number;

    constructor(private route: ActivatedRoute, private ciService: CIService) {}

    ngOnInit(): void {
        this.ciId = Number(this.route.snapshot.paramMap.get('id'));
        this.ciService.getById(this.ciId).subscribe({
            next: (ci) => {
                this.ci.set(ci);
                this.loading.set(false);
            },
            error: () => {
                this.notFound.set(true);
                this.loading.set(false);
            },
        });
    }

    protected severityClass(severity: string): string {
        return `chip chip-severity-${(severity || '').toLowerCase()}`;
    }

    protected statusClass(status: string): string {
        return `chip chip-status-${(status || '').toLowerCase()}`;
    }

    protected slaClass(state: string): string {
        const map: Record<string, string> = { on_track: 'low', met: 'low', at_risk: 'medium', breached: 'critical' };
        return `chip chip-severity-${map[state] ?? ''}`;
    }
}
