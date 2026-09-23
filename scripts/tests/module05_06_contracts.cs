using NullableDemo;
internal static class Contracts
{
static void Check(bool condition,string message){if(!condition)throw new Exception(message);}
static void Throws<T>(Action action) where T:Exception{try{action();}catch(T){return;}throw new Exception("Expected "+typeof(T).Name);}
static async Task ThrowsAsync<T>(Func<Task> action) where T:Exception{try{await action();}catch(T){return;}throw new Exception("Expected "+typeof(T).Name);}
public static void Main(){
var c=new Customer("A",null,null);Check(c.Email is null&&c.Address is null,"optional");c.AssignFallbackEmail(" A@B.COM ");c.AssignFallbackEmail("z@b.com");Check(c.Email=="a@b.com","fallback overwrote");Check(CustomerSearch.FindByEmail([c]," A@B.COM ")==c,"normalization");Check(CustomerSearch.FindByEmail([c],"no@b.com") is null,"not found");Throws<ArgumentNullException>(()=>new Customer(null!,null,null));
}
}
