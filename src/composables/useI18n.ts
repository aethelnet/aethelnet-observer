import { t as translate, setLocale as setLoc, getLocale as getLoc } from '../i18n'

export function useI18n() {
    return {
        t: translate,
        setLocale: setLoc,
        getLocale: getLoc
    }
}
