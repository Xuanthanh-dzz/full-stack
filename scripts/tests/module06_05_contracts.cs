using OpenClosedDemo;
internal static class Contracts
{
 static void Check(bool ok,string why){if(!ok)throw new InvalidOperationException(why);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new InvalidOperationException("Expected "+typeof(T).Name);}
 static void Main(){

 var from=new DateOnly(2026,7,1);var to=new DateOnly(2026,7,31);var rule=new SeasonalDiscountRule("s",from,to,100,30);
 Check(rule.ComputeDiscount(new Cart("x",100,1,from))==30 && rule.ComputeDiscount(new Cart("x",100,1,to))==30,"inclusive dates");
 Check(rule.ComputeDiscount(new Cart("x",100,1,to.AddDays(1)))==0,"outside date");
 var rules=new List<IDiscountRule>();var engine=new DiscountEngine(rules,.1m);var cart=new Cart("gold",100,5,from);Check(engine.Apply(cart).Amount==0,"no rules");
 rules.Add(new ConstantRule(100));Check(engine.Apply(cart).Amount==10,"live config and cap");
 Check(new DiscountEngine(rules,1).Apply(cart with {Subtotal=.6m}).Amount==.6m,"rounded cap never exceeds subtotal");
 Throws<ArgumentOutOfRangeException>(()=>engine.Apply(cart with {Subtotal=-1}));Throws<ArgumentOutOfRangeException>(()=>new DiscountEngine(rules,2));

 }
 sealed class ConstantRule(decimal amount):IDiscountRule {public string Code=>"fixed";public decimal ComputeDiscount(Cart c)=>amount;}
}
