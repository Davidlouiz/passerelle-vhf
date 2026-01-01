import asyncio
import httpx

async def test_key(key, description):
    print(f"\n{description}")
    print(f"Clé: {key}")
    test_url = f"https://data.ffvl.fr/api/?base=balises&r=list&mode=json&key={key}"
    
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(test_url)
            
            try:
                data = response.json()
                is_valid = isinstance(data, list) and len(data) > 0
                print(f"  → JSON valide: type={type(data).__name__}, longueur={len(data) if isinstance(data, list) else 'N/A'}")
                print(f"  → Résultat: {'✓ VALIDE' if is_valid else '✗ INVALIDE'}")
                return is_valid
            except Exception as e:
                print(f"  → Pas du JSON: {response.text[:100]}")
                print(f"  → Résultat: ✗ INVALIDE")
                return False
    except Exception as e:
        print(f"  → Erreur: {e}")
        return False

async def main():
    print("=== Test de validation de clés FFVL ===")
    
    await test_key("ead3c968a45ad9ec14cbb67373be1e19", "Test 1: Clé valide")
    await test_key("00000000000000000000000000000000", "Test 2: Clé invalide (zéros)")
    await test_key("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "Test 3: Clé invalide (bon format)")
    await test_key("invalid", "Test 4: Clé trop courte")
    await test_key("", "Test 5: Clé vide")

if __name__ == "__main__":
    asyncio.run(main())
