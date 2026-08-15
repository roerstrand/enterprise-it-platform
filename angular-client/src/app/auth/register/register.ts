import { Component, signal } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { UserService } from '../../users/user.service';
import { AuthService } from '../auth.service';

@Component({
    selector: 'app-register',
    imports: [
        ReactiveFormsModule,
        RouterLink,
        MatFormFieldModule,
        MatInputModule,
        MatButtonModule,
        MatCardModule,
        MatIconModule,
        MatProgressSpinnerModule,
    ],
    templateUrl: './register.html',
    styleUrl: '../login/login.scss',
})
export class Register {
    protected readonly form: FormGroup;
    protected readonly loading = signal(false);
    protected readonly error = signal<string | null>(null);

    constructor(
        formBuilder: FormBuilder,
        private userService: UserService,
        private authService: AuthService,
        private router: Router,
    ) {
        this.form = formBuilder.group({
            name: ['', Validators.required],
            email: ['', [Validators.required, Validators.email]],
            password: ['', [Validators.required, Validators.minLength(8)]],
        });
    }

    protected onSubmit(): void {
        if (this.form.invalid) return;
        this.loading.set(true);
        this.error.set(null);
        const { name, email, password } = this.form.value;
        // Nya kontot får alltid rollen "viewer" server-side (självregistrering), oavsett vad som skickas.
        this.userService.create(name, email, password).subscribe({
            next: () => {
                // Logga in direkt så användaren slipper skriva in uppgifterna igen
                this.authService.login(email, password).subscribe({
                    next: () => this.router.navigateByUrl('/'),
                    error: () => {
                        this.loading.set(false);
                        this.router.navigate(['/login']);
                    },
                });
            },
            error: (err) => {
                this.loading.set(false);
                this.error.set(
                    err.status === 409
                        ? 'That email is already registered. Try logging in instead.'
                        : 'Could not create account. Please try again.'
                );
            },
        });
    }
}
