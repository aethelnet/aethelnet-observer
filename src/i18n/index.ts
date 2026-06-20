import { reactive } from 'vue'
import en from './locales/en'
import de from './locales/de'

// Define allowed locale types
type Locale = 'en' | 'de'
type Messages = typeof en

const state = reactive({
    locale: 'en' as Locale,
    messages: {
        en,
        de
    } as Record<string, any>
})

export function t(key: string, params?: Record<string, any>): string {
    const keys = key.split('.')
    let value: any = state.messages[state.locale]

    // Traverse key path
    for (const k of keys) {
        if (value && typeof value === 'object' && k in value) {
            value = value[k]
        } else {
            // Fallback to EN if missing in current locale
            if (state.locale !== 'en') {
                let fallback: any = state.messages['en']
                for (const fbK of keys) {
                    if (fallback && typeof fallback === 'object' && fbK in fallback) {
                        fallback = fallback[fbK]
                    } else {
                        return key // Missing in fallback too
                    }
                }
                value = fallback
            } else {
                return key // Missing in default locale
            }
        }
    }

    if (typeof value !== 'string') return key

    // Interpolation: {{param}}
    if (params) {
        return value.replace(/\{\{(\w+)\}\}/g, (_, match) => {
            return params[match] !== undefined ? String(params[match]) : `{{${match}}}`
        })
    }

    return value
}

export function setLocale(locale: string) {
    if (state.messages[locale]) {
        state.locale = locale as Locale
    } else {
        console.warn(`[i18n] Locale ${locale} not found.`)
    }
}

export function getLocale(): string {
    return state.locale
}
